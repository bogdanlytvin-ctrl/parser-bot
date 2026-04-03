"""
RSS / Atom feed parser + Google News RSS.

source_url examples:
  https://feeds.bbci.co.uk/news/rss.xml
  https://news.google.com/rss/search?q=bitcoin&hl=uk&gl=UA&ceid=UA:uk
"""
import logging
import re

import aiohttp
import feedparser

from parsers import ParsedItem

logger = logging.getLogger(__name__)


def google_news_url(query: str, lang: str = "uk") -> str:
    import urllib.parse
    q = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl={lang}&gl=UA&ceid=UA:{lang}"


async def parse(session: aiohttp.ClientSession,
                source_url: str,
                keywords: list[str],
                limit: int = 10) -> list[ParsedItem]:
    try:
        async with session.get(
            source_url,
            timeout=aiohttp.ClientTimeout(total=15),
            headers={"User-Agent": "Mozilla/5.0 (compatible; ParserBot/1.0)"},
        ) as resp:
            if resp.status != 200:
                logger.warning("RSS %s → %d", source_url, resp.status)
                return []
            content = await resp.read()
    except Exception as e:
        logger.error("RSS fetch error %s: %s", source_url, e)
        return []

    feed = feedparser.parse(content)
    items: list[ParsedItem] = []

    for entry in feed.entries[:50]:
        title = _clean(entry.get("title", ""))
        desc  = _clean(entry.get("summary", ""))
        url   = entry.get("link", "")
        pub   = entry.get("published", "") or entry.get("updated", "")

        if not url or not title:
            continue

        # Keyword filter
        if keywords and not _matches(f"{title} {desc}", keywords):
            continue

        items.append(ParsedItem(
            url=url, title=title,
            description=desc[:300],
            pub_date=pub,
        ))
        if len(items) >= limit:
            break

    return items


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def _matches(text: str, keywords: list[str]) -> bool:
    tl = text.lower()
    return any(kw.lower() in tl for kw in keywords)
