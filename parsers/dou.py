"""
DOU.ua vacancy parser.

source_url: category/technology filter, e.g. "Python" or "JavaScript"
API: https://jobs.dou.ua/vacancies/feeds/?category=Python
"""
import logging

import aiohttp
import feedparser

from parsers import ParsedItem

logger = logging.getLogger(__name__)

RSS_BASE = "https://jobs.dou.ua/vacancies/feeds/"


def build_url(query: str) -> str:
    """query = category like 'Python', 'JavaScript', 'QA', etc."""
    import urllib.parse
    return f"{RSS_BASE}?category={urllib.parse.quote(query)}"


async def parse(session: aiohttp.ClientSession,
                source_url: str,
                keywords: list[str],
                limit: int = 10) -> list[ParsedItem]:

    url = source_url if source_url.startswith("http") else build_url(source_url)

    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=15),
            headers={"User-Agent": "Mozilla/5.0"},
        ) as resp:
            if resp.status != 200:
                logger.warning("DOU %s → %d", url, resp.status)
                return []
            content = await resp.read()
    except Exception as e:
        logger.error("DOU fetch error: %s", e)
        return []

    feed = feedparser.parse(content)
    items: list[ParsedItem] = []

    for entry in feed.entries[:50]:
        title = entry.get("title", "")
        desc  = entry.get("summary", "")
        href  = entry.get("link", "")
        pub   = entry.get("published", "")

        if not title or not href:
            continue

        # Extract salary if present
        import re
        salary = ""
        sal_match = re.search(r"\$[\d\s,]+", title + " " + desc)
        if sal_match:
            salary = sal_match.group(0).strip()

        # Keyword filter
        if keywords and not _matches(f"{title} {desc}", keywords):
            continue

        items.append(ParsedItem(
            url=href, title=title,
            description=_clean(desc)[:400],
            price=salary,
            pub_date=pub,
        ))
        if len(items) >= limit:
            break

    return items


def _clean(text: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def _matches(text: str, keywords: list[str]) -> bool:
    tl = text.lower()
    return any(kw.lower() in tl for kw in keywords)
