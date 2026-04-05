"""
Telegram public channel parser.
Scrapes https://t.me/s/{channel} — the public preview page.
Works only for PUBLIC channels with preview enabled.
"""
import logging
import re

import aiohttp
from bs4 import BeautifulSoup

from parsers import ParsedItem

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


async def parse(session: aiohttp.ClientSession,
                source_url: str,
                keywords: list[str],
                limit: int = 10) -> list[ParsedItem]:
    """
    source_url: @channel_name or t.me/channel_name or just channel_name
    """
    channel = _normalize(source_url)
    if not channel:
        logger.warning("Telegram: invalid channel: %s", source_url)
        return []

    url = f"https://t.me/s/{channel}"
    try:
        async with session.get(
            url, headers=_HEADERS,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status != 200:
                logger.warning("Telegram channel %s -> %d", channel, resp.status)
                return []
            html = await resp.text()
    except Exception as e:
        logger.error("Telegram channel fetch error %s: %s", channel, e)
        return []

    return _parse_html(html, channel, keywords, limit)


def _normalize(src: str) -> str:
    src = src.strip()
    src = src.lstrip("@")
    src = src.replace("https://t.me/", "").replace("http://t.me/", "")
    src = src.replace("t.me/", "").rstrip("/")
    if src.startswith("s/"):
        src = src[2:]
    return src


def _parse_html(html: str, channel: str, keywords: list[str], limit: int) -> list[ParsedItem]:
    soup = BeautifulSoup(html, "html.parser")
    messages = soup.select(".tgme_widget_message")
    items: list[ParsedItem] = []

    for msg in reversed(messages):  # newest last -> process newest first
        text_el = msg.select_one(".tgme_widget_message_text")
        text = text_el.get_text(separator=" ").strip() if text_el else ""
        if not text:
            continue

        msg_link = msg.select_one("a.tgme_widget_message_date")
        url = msg_link["href"] if msg_link and msg_link.get("href") else ""
        if not url:
            continue

        time_el = msg.select_one("time")
        pub_date = time_el.get("datetime", "") if time_el else ""

        image_url = ""
        photo_el = msg.select_one(".tgme_widget_message_photo_wrap")
        if photo_el:
            style = photo_el.get("style", "")
            m = re.search(r"url\(['\"]?(https?://[^'\")\s]+)['\"]?\)", style)
            if m:
                image_url = m.group(1)

        if keywords and not _matches(text, keywords):
            continue

        title = text[:100].replace("\n", " ")
        desc  = text[:400]

        items.append(ParsedItem(
            url=url,
            title=title,
            description=desc,
            image_url=image_url,
            pub_date=pub_date,
        ))

        if len(items) >= limit:
            break

    return items


def _matches(text: str, keywords: list[str]) -> bool:
    tl = text.lower()
    return any(kw.lower() in tl for kw in keywords)
