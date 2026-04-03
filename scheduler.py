"""
Background scheduler — runs due tasks and dispatches results to Telegram.
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

logger = logging.getLogger(__name__)

SCAN_INTERVAL = int(os.getenv("SCHEDULER_INTERVAL_SEC", 60))

SendFn = Callable[[str, str, str], Awaitable[None]]
# send_fn(channel_id, text, photo_url)

PARSER_MAP = {
    "rss":     rss.parse,
    "google":  rss.parse,   # Google News is also RSS
    "olx":     olx.parse,
    "rozetka": rozetka.parse,
    "dou":     dou.parse,
    "web":     web.parse,
}

SOURCE_NAMES = {
    "rss":     "RSS",
    "google":  "Google News",
    "olx":     "OLX",
    "rozetka": "Rozetka",
    "dou":     "DOU Jobs",
    "web":     "Сайт",
}


async def run_scheduler(send_fn: SendFn) -> None:
    logger.info("Scheduler started. Interval: %ds", SCAN_INTERVAL)
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await _tick(session, send_fn)
            except asyncio.CancelledError:
                logger.info("Scheduler cancelled.")
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
            # Update schedule regardless of success/failure
            now      = datetime.now(timezone.utc)
            next_run = now + timedelta(minutes=task["interval_min"])
            db.update_task_schedule(
                task["id"],
                now.isoformat(),
                next_run.isoformat(),
            )


async def _run_task(session: aiohttp.ClientSession,
                    task: db.sqlite3.Row,
                    send_fn: SendFn) -> None:
    source_type = task["source_type"]
    parse_fn    = PARSER_MAP.get(source_type)
    if not parse_fn:
        logger.warning("Unknown source_type: %s", source_type)
        return

    keywords = [k.strip() for k in (task["keywords"] or "").split(",") if k.strip()]
    source_url = task["source_url"] or ""

    # For Google News — build RSS URL from query
    if source_type == "google":
        source_url = rss.google_news_url(source_url)

    items: list[ParsedItem] = await parse_fn(session, source_url, keywords, limit=5)

    new_count = 0
    for item in items:
        hash_val = item.make_hash()
        is_new = db.save_result(
            task_id=task["id"],
            url=item.url,
            title=item.title,
            description=item.description,
            price=item.price,
            image_url=item.image_url,
            pub_date=item.pub_date,
            hash_val=hash_val,
        )
        if not is_new:
            continue

        new_count += 1
        msg = _format_message(task, item)
        await send_fn(task["channel_id"], msg, item.image_url)
        await asyncio.sleep(0.5)   # Telegram rate limit

    if new_count:
        logger.info("Task '%s': sent %d new items", task["name"], new_count)


def _format_message(task: db.sqlite3.Row, item: ParsedItem) -> str:
    source = SOURCE_NAMES.get(task["source_type"], task["source_type"])
    lines = [
        f"📌 <b>{_esc(item.title)}</b>",
        "",
        f"📂 <i>{_esc(task['name'])}</i>  |  {source}",
    ]

    if item.price:
        lines.append(f"💰 {_esc(item.price)}")

    if item.description:
        lines.append("")
        lines.append(_esc(item.description[:300]))

    if item.pub_date:
        lines.append(f"\n🕐 {item.pub_date[:16]}")

    lines.append(f"\n🔗 <a href=\"{item.url}\">Відкрити</a>")
    return "\n".join(lines)


def _esc(text: str) -> str:
    """Escape HTML special chars."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))
