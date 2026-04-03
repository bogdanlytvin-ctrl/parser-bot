"""
Generic website parser — scrapes any page with BeautifulSoup.

source_url: full URL of the page to scrape.
keywords: filter results by keywords.

Strategy:
  1. Look for article/news cards (common patterns)
  2. Look for <a> links with meaningful text
  3. Deduplicate by URL
"""
import logging
import re
import urllib.parse

import aiohttp
from bs4 import BeautifulSoup, Tag

from parsers import ParsedItem

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
}

# CSS selectors tried in order for finding article cards
CARD_SELECTORS = [
    "article",
    "[class*='card']",
    "[class*='item']",
    "[class*='post']",
    "[class*='news']",
    "[class*='listing']",
    "li.result",
]

TITLE_SELECTORS = ["h1", "h2", "h3", "h4", "[class*='title']", "[class*='heading']"]
DESC_SELECTORS  = ["p", "[class*='desc']", "[class*='text']", "[class*='summary']"]
PRICE_SELECTORS = ["[class*='price']", "[class*='cost']", "[class*='amount']"]
IMG_SELECTORS   = ["img[src]"]


async def parse(session: aiohttp.ClientSession,
                source_url: str,
                keywords: list[str],
                limit: int = 10) -> list[ParsedItem]:
    try:
        async with session.get(
            source_url,
            headers=HEADERS,
            timeout=aiohttp.ClientTimeout(total=20),
            allow_redirects=True,
        ) as resp:
            if resp.status != 200:
                logger.warning("Web %s → %d", source_url, resp.status)
                return []
            html = await resp.text(errors="replace")
    except Exception as e:
        logger.error("Web fetch error %s: %s", source_url, e)
        return []

    soup = BeautifulSoup(html, "html.parser")
    base = _base_url(source_url)

    # Remove noise
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    items: list[ParsedItem] = []
    seen_urls: set[str] = set()

    # Try structured cards first
    cards = _find_cards(soup)

    if cards:
        for card in cards[:50]:
            item = _extract_from_card(card, base)
            if not item or item.url in seen_urls:
                continue
            if keywords and not _matches(f"{item.title} {item.description}", keywords):
                continue
            seen_urls.add(item.url)
            items.append(item)
            if len(items) >= limit:
                break
    else:
        # Fallback: collect all meaningful links
        for a in soup.find_all("a", href=True):
            href = _abs_url(a["href"], base)
            if not href or href in seen_urls:
                continue
            title = a.get_text(strip=True)
            if len(title) < 15:   # skip nav/footer links
                continue
            if keywords and not _matches(title, keywords):
                continue
            seen_urls.add(href)
            items.append(ParsedItem(url=href, title=title[:200]))
            if len(items) >= limit:
                break

    return items


def _find_cards(soup: BeautifulSoup) -> list[Tag]:
    for sel in CARD_SELECTORS:
        cards = soup.select(sel)
        if len(cards) >= 2:
            return cards
    return []


def _extract_from_card(card: Tag, base: str) -> ParsedItem | None:
    # Title
    title = ""
    for sel in TITLE_SELECTORS:
        el = card.select_one(sel)
        if el:
            title = el.get_text(strip=True)
            if title:
                break

    # URL
    href = ""
    link = card.select_one("a[href]")
    if link:
        href = _abs_url(link.get("href", ""), base)
    if not href and title:
        # Try parent
        parent = card.find_parent("a")
        if parent:
            href = _abs_url(parent.get("href", ""), base)

    if not title or not href:
        return None

    # Description
    desc = ""
    for sel in DESC_SELECTORS:
        el = card.select_one(sel)
        if el:
            t = el.get_text(strip=True)
            if len(t) > 20:
                desc = t[:300]
                break

    # Price
    price = ""
    for sel in PRICE_SELECTORS:
        el = card.select_one(sel)
        if el:
            price = el.get_text(strip=True)[:50]
            break

    # Image
    img = ""
    img_el = card.select_one("img[src]")
    if img_el:
        img = _abs_url(img_el.get("src", ""), base)

    return ParsedItem(
        url=href, title=title[:200],
        description=desc, price=price, image_url=img,
    )


def _base_url(url: str) -> str:
    p = urllib.parse.urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _abs_url(href: str, base: str) -> str:
    if not href or href.startswith(("javascript:", "mailto:", "#")):
        return ""
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return base + href
    return base + "/" + href


def _matches(text: str, keywords: list[str]) -> bool:
    tl = text.lower()
    return any(kw.lower() in tl for kw in keywords)


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())
