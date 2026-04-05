"""
Background scheduler — runs due tasks and dispatches results to Telegram.
AI filtering via Claude Haiku (optional per task).
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Callable, Awaitable

import aiohttp

import database as db
from parsers import ParsedItem
from parsers import rss, olx, rozetka, dou, web
from parsers import telegram_channel

logger = logging.getLogger(__name__)

SCAN_INTERVAL     = int(os.getenv("SCHEDULER_INTERVAL_SEC", "60"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SendFn = Callable[[str, str, str], Awaitable[None]]

PARSER_MAP = {
    "rss":      rss.parse,
    "google":   rss.parse,
    "olx":      olx.parse,
    "rozetka":  rozetka.parse,
    "dou":      dou.parse,
    "web":      web.parse,
    "telegram": telegram_channel.parse,
}

SOURCE_NAMES = {
    "rss":      "RSS",
    "google":   "Google News",
    "olx":      "OLX",
    "rozetka":  "Rozetka",
    "dou":      "DOU Jobs",
    "web":      "Сайт",
    "telegram": "Telegram",
}

COUNTRY_FLAGS = {
    "ua": "🇺🇦", "us": "🇺🇸", "eu": "🇪🇺", "ca": "🇨🇦", "world": "🌍",
}


async def run_scheduler(send_fn: SendFn) -> None:
    logger.info("Scheduler started. Interval: %ds, AI filter: %s",
                SCAN_INTERVAL, "enabled" if ANTHROPIC_API_KEY else "disabled (no API key)")
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await _tick(session, send_fn)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Scheduler tick error: %s", e, exc_info=True)
            await asyncio.sleep(SCAN_INTERVAL)


async def _tick(session: aiohttp.ClientSession, send_fn: SendFn) -> None:
    tasks = db.get_due_tasks()
    if not tasks:
        return

    logger.info("Running %d due tasks", len(tasks))
    for task in tasks:
        try:
            await _run_task(session, task, send_fn)
        except Exception as e:
            logger.error("Task %d error: %s", task["id"], e, exc_info=True)
        finally:
            now      = datetime.now(timezone.utc)
            next_run = now + timedelta(minutes=task["interval_min"])
            db.update_task_schedule(task["id"], now.isoformat(), next_run.isoformat())


async def _run_task(session: aiohttp.ClientSession,
                    task: db.sqlite3.Row, send_fn: SendFn) -> None:
    source_type = task["source_type"]
    parse_fn    = PARSER_MAP.get(source_type)
    if not parse_fn:
        logger.warning("Unknown source_type: %s", source_type)
        return

    keywords   = [k.strip() for k in (task["keywords"] or "").split(",") if k.strip()]
    source_url = task["source_url"] or ""
    country    = task["country"] or "ua"
    ai_filter  = bool(task["ai_filter"])

    # Build proper URL for Google News with country support
    if source_type == "google":
        source_url = rss.google_news_url(source_url, country=country)

    items: list[ParsedItem] = await parse_fn(session, source_url, keywords, limit=5)

    new_count = 0
    for item in items:
        hash_val = item.make_hash()
        is_new = db.save_result(
            task_id=task["id"], url=item.url, title=item.title,
            description=item.description, price=item.price,
            image_url=item.image_url, pub_date=item.pub_date, hash_val=hash_val,
        )
        if not is_new:
            continue

        # AI relevance check (if enabled and API key present)
        if ai_filter and ANTHROPIC_API_KEY:
            relevant = await _ai_filter(session, item, task)
            if not relevant:
                logger.debug("AI filtered out: %s", item.title[:60])
                continue

        msg = _format_message(task, item, country)
        await send_fn(task["channel_id"], msg, item.image_url)
        await asyncio.sleep(0.5)
        new_count += 1

    if new_count:
        logger.info("Task '%s': sent %d new items", task["name"], new_count)


async def _ai_filter(session: aiohttp.ClientSession,
                     item: ParsedItem, task: db.sqlite3.Row) -> bool:
    """
    Ask Claude Haiku whether this item is relevant to the task.
    Returns True if relevant, False if should be skipped.
    """
    task_name = task["name"]
    keywords  = task["keywords"] or ""
    niche     = task["niche"] or ""

    prompt = (
        f"Task: '{task_name}' (niche: {niche}, keywords: {keywords})\n"
        f"Article title: {item.title}\n"
        f"Article description: {item.description[:200]}\n\n"
        "Is this article relevant to the task? Reply only: YES or NO"
    )

    try:
        async with session.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":      "claude-haiku-4-5-20251001",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                logger.debug("AI filter API error: %s", resp.status)
                return True  # on error — allow through
            data = await resp.json()
            answer = data["content"][0]["text"].strip().upper()
            return "YES" in answer
    except Exception as e:
        logger.debug("AI filter exception: %s", e)
        return True  # on error — allow through


def _format_message(task: db.sqlite3.Row, item: ParsedItem, country: str) -> str:
    source = SOURCE_NAMES.get(task["source_type"], task["source_type"])
    flag   = COUNTRY_FLAGS.get(country, "")

    lines = [f"📌 <b>{_esc(item.title)}</b>", ""]

    # Source line with flag
    lines.append(f"📂 <i>{_esc(task['name'])}</i>  {flag}  {source}")

    if item.price:
        lines.append(f"💰 {_esc(item.price)}")

    if item.description and item.description != item.title:
        # Truncate to 350 chars, cut at last word
        desc = item.description[:350]
        if len(item.description) > 350:
            desc = desc.rsplit(" ", 1)[0] + "…"
        lines += ["", _esc(desc)]

    if item.pub_date:
        lines.append(f"\n🕐 {item.pub_date[:16]}")

    lines.append(f"\n🔗 <a href=\"{item.url}\">Читати далі</a>")
    return "\n".join(lines)


def _esc(text: str) -> str:
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))
