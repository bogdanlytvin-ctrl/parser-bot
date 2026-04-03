"""
OLX Ukraine parser — scrapes search results page.

source_url: search query string, e.g. "квартира оренда Київ"
We build the OLX search URL internally.
"""
import logging
import re
import urllib.parse

import aiohttp
from bs4 import BeautifulSoup

from parsers import ParsedItem

logger = logging.getLogger(__name__)

BASE = "https://www.olx.ua/uk/list/q-{query}/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "uk-UA,uk;q=0.9",
}


def build_url(query: str) -> str:
    q = urllib.parse.quote_plus(query)
    return f"https://www.olx.ua/uk/list/q-{q}/"


async def parse(session: aiohttp.ClientSession,
                source_url: str,
                keywords: list[str],
                limit: int = 10) -> list[ParsedItem]:
    """
    source_url: either full OLX URL or a search query string.
    """
    # If it's a query (not a URL) — build URL
    url = source_url if source_url.startswith("http") else build_url(source_url)

    try:
        async with session.get(
            url,
            headers=HEADERS,
            timeout=aiohttp.ClientTimeout(total=20),
        ) as resp:
            if resp.status != 200:
                logger.warning("OLX %s → %d", url, resp.status)
                return []
            html = await resp.text()
    except Exception as e:
        logger.error("OLX fetch error: %s", e)
        return []

    soup = BeautifulSoup(html, "html.parser")
    items: list[ParsedItem] = []

    # OLX listings cards
    cards = soup.select("[data-cy='l-card']")
    if not cards:
        # Fallback selector
        cards = soup.select("div.css-1sw7q4x")

    for card in cards[:50]:
        # Title
        title_el = card.select_one("h6") or card.select_one("[data-cy='ad-card-title']")
        title = title_el.get_text(strip=True) if title_el else ""

        # URL
        link_el = card.select_one("a[href]")
        href = link_el["href"] if link_el else ""
        if href and not href.startswith("http"):
            href = "https://www.olx.ua" + href

        # Price
        price_el = card.select_one("[data-testid='ad-price']") or card.select_one(".price-label")
        price = price_el.get_text(strip=True) if price_el else ""

        # Description
        desc_el = card.select_one("p.css-6g2e8n") or card.select_one("[data-cy='ad-card-description']")
        desc = desc_el.get_text(strip=True) if desc_el else ""

        # Image
        img_el = card.select_one("img")
        img = img_el.get("src", "") if img_el else ""

        if not title or not href:
            continue

        # Keyword filter
        if keywords and not _matches(f"{title} {desc}", keywords):
            continue

        items.append(ParsedItem(
            url=href, title=title,
            description=desc[:300],
            price=price,
            image_url=img,
        ))
        if len(items) >= limit:
            break

    return items


def _matches(text: str, keywords: list[str]) -> bool:
    tl = text.lower()
    return any(kw.lower() in tl for kw in keywords)
