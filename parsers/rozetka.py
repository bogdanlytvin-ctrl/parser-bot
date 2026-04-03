"""
Rozetka parser — uses Rozetka's public search API.

source_url: search query, e.g. "iphone 14 128gb"
"""
import logging
import urllib.parse

import aiohttp

from parsers import ParsedItem

logger = logging.getLogger(__name__)

API = "https://search.rozetka.com.ua/ua/search/api/v6/"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


async def parse(session: aiohttp.ClientSession,
                source_url: str,
                keywords: list[str],
                limit: int = 10) -> list[ParsedItem]:
    query = source_url if not source_url.startswith("http") else source_url

    try:
        async with session.get(
            API,
            params={
                "text":     query,
                "page":     1,
                "per_page": min(limit * 2, 24),
                "country":  "UA",
                "lang":     "ua",
            },
            headers=HEADERS,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status != 200:
                logger.warning("Rozetka API %d", resp.status)
                return []
            data = await resp.json()
    except Exception as e:
        logger.error("Rozetka fetch error: %s", e)
        return []

    goods = data.get("data", {}).get("goods", []) or []
    items: list[ParsedItem] = []

    for g in goods:
        title = g.get("title", "")
        price = str(g.get("price", ""))
        old_price = str(g.get("old_price", ""))
        href  = g.get("href", "") or f"https://rozetka.com.ua/ua/{g.get('id','')}/p{g.get('id','')}"
        img   = (g.get("images") or [{}])[0].get("url", "") if g.get("images") else ""

        if not title:
            continue

        price_str = f"{price} грн"
        if old_price and old_price != "0" and old_price != price:
            price_str += f" (було {old_price} грн)"

        desc = g.get("description", "") or ""

        # Keyword filter
        if keywords and not _matches(f"{title} {desc}", keywords):
            continue

        items.append(ParsedItem(
            url=href, title=title,
            description=desc[:300],
            price=price_str,
            image_url=img,
        ))
        if len(items) >= limit:
            break

    return items


def _matches(text: str, keywords: list[str]) -> bool:
    tl = text.lower()
    return any(kw.lower() in tl for kw in keywords)
