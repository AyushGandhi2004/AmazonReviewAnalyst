"""ScrapingBee-based Amazon product listing scraper."""

import json
import logging
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup, Tag

from config import settings
from models import ProductMetadata

logger = logging.getLogger(__name__)

SCRAPINGBEE_ENDPOINT = "https://app.scrapingbee.com/api/v1/"
AMAZON_PRODUCT_URL = "https://www.amazon.in/dp/{asin}"


async def scrape_product_listing(asin: str) -> ProductMetadata:
    """Scrape product metadata for a single ASIN using ScrapingBee.

    Fetches the Amazon product page via ScrapingBee, parses the HTML with
    BeautifulSoup, and returns a standardised ProductMetadata object. Every
    field defaults to None if it cannot be extracted, so the shape is always
    stable regardless of what Amazon returns.

    Args:
        asin: The Amazon ASIN to scrape.

    Returns:
        A ProductMetadata instance with all available fields populated.

    Raises:
        RuntimeError: If the ScrapingBee request fails or returns an error status.
    """
    url = AMAZON_PRODUCT_URL.format(asin=asin)
    html = await _fetch_via_scrapingbee(url, asin)
    # lxml is faster but optional; html.parser is always available
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
    temp=_parse_product_page(asin, url, soup)
    print("Scrapped Response:")
    print(temp)
    return temp


async def _fetch_via_scrapingbee(url: str, asin: str) -> str:
    """Make a GET request through ScrapingBee and return the raw HTML.

    Args:
        url: The Amazon product page URL to fetch.
        asin: Used only for logging context.

    Returns:
        Raw HTML string of the page.

    Raises:
        RuntimeError: If the HTTP request fails or ScrapingBee returns an error.
    """
    params = {
        "api_key": settings.scrapingbee_api_key,
        "url": url,
        "render_js": "false",
        "premium_proxy": "true",
        "country_code": "us",
        "block_ads": "true",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(SCRAPINGBEE_ENDPOINT, params=params)

        if response.status_code == 401:
            raise RuntimeError("ScrapingBee: invalid API key (401).")
        if response.status_code == 402:
            raise RuntimeError("ScrapingBee: account out of credits (402).")
        if response.status_code != 200:
            raise RuntimeError(
                f"ScrapingBee returned HTTP {response.status_code} for ASIN {asin}. "
                f"Body: {response.text[:300]}"
            )

        return response.text

    except httpx.RequestError as exc:
        raise RuntimeError(f"Network error fetching ASIN {asin} via ScrapingBee: {exc}") from exc


def _parse_product_page(asin: str, url: str, soup: BeautifulSoup) -> ProductMetadata:
    """Extract all fields from a parsed Amazon product page.

    Each extraction is isolated so a failure on one field never prevents
    the others from being populated.

    Args:
        asin: The product ASIN, used as the primary identifier.
        url: Original product URL, stored for reference.
        soup: Parsed BeautifulSoup tree of the product page.

    Returns:
        A ProductMetadata instance with all extractable fields populated.
    """
    return ProductMetadata(
        asin=asin,
        product_url=url,
        title=_extract_title(soup),
        price=_extract_price(soup),
        star_rating=_extract_star_rating(soup),
        total_reviews=_extract_total_reviews(soup),
        bsr=_extract_bsr(soup),
        bullet_points=_extract_bullet_points(soup),
        specifications=_extract_specifications(soup),
        image_url=_extract_image_url(soup),
    )


def _extract_title(soup: BeautifulSoup) -> Optional[str]:
    """Extract the product title."""
    selectors = ["#productTitle", "span#productTitle", "h1#title span"]
    for sel in selectors:
        node = soup.select_one(sel)
        if node and node.get_text(strip=True):
            return node.get_text(strip=True)
    return None


def _extract_price(soup: BeautifulSoup) -> Optional[str]:
    """Extract the product price as a raw string (e.g. '$29.99')."""
    selectors = [
        ".apexPriceToPay span.a-offscreen",
        ".a-price .a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        "#price_inside_buybox",
        "#corePrice_feature_div .a-offscreen",
        "#tp_price_block_total_price_ww .a-offscreen",
    ]
    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            text = node.get_text(strip=True)
            if text and ("₹"in text or"$" in text or "£" in text or "€" in text or text[0].isdigit()):
                return text
    return None


def _extract_star_rating(soup: BeautifulSoup) -> Optional[float]:
    """Extract the average star rating as a float (e.g. 4.3)."""
    selectors = [
        "#acrPopover .a-icon-alt",
        "span[data-hook='rating-out-of-text']",
        "i.a-icon-star span.a-icon-alt",
        "#averageCustomerReviews .a-icon-alt",
    ]
    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            text = node.get_text(strip=True)
            match = re.search(r"(\d+\.?\d*)\s+out of", text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
    return None


def _extract_total_reviews(soup: BeautifulSoup) -> Optional[int]:
    """Extract the total number of customer ratings as an integer."""
    selectors = [
        "#acrCustomerReviewText",
        "span[data-hook='total-review-count']",
        "#averageCustomerReviews #acrCustomerReviewText",
    ]
    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            text = node.get_text(strip=True)
            # Text looks like "1,234 ratings" or "1,234 global ratings"
            digits = re.sub(r"[^\d]", "", text.split()[0])
            if digits:
                try:
                    return int(digits)
                except ValueError:
                    continue
    return None


def _extract_bsr(soup: BeautifulSoup) -> Optional[str]:
    """Extract the Best Sellers Rank string (e.g. '#1,234 in Electronics')."""
    # BSR appears in a few different page layouts; search all text nodes
    for candidate in soup.find_all(string=re.compile(r"Best Sellers Rank", re.I)):
        parent = candidate.find_parent()
        if parent is None:
            continue
        # Grab the sibling or parent text that contains the actual rank
        container = parent.find_parent(["li", "tr", "div", "span"])
        if container:
            raw = container.get_text(" ", strip=True)
            # Extract up to the first newline / pipe to keep it concise
            rank_match = re.search(r"#[\d,]+\s+in\s+[\w\s&]+", raw)
            if rank_match:
                return rank_match.group(0).strip()
            # Fallback: return full container text trimmed
            return raw[:120]
    return None


def _extract_bullet_points(soup: BeautifulSoup) -> list[str]:
    """Extract the feature bullet points from the product listing."""
    bullets: list[str] = []
    selectors = [
        "#feature-bullets ul li span.a-list-item",
        "#featurebullets_feature_div ul li span.a-list-item",
        "#feature-bullets li:not(.aok-hidden) span",
    ]
    for sel in selectors:
        nodes = soup.select(sel)
        if nodes:
            for node in nodes:
                text = node.get_text(strip=True)
                if text and len(text) > 5 and "Make sure this fits" not in text:
                    bullets.append(text)
            if bullets:
                break
    return bullets[:10]  # cap at 10 bullet points


def _extract_image_url(soup: BeautifulSoup) -> Optional[str]:
    """Extract the main product image URL.

    Amazon embeds a JSON map of {url: [width, height]} in the
    data-a-dynamic-image attribute of #landingImage. We pick the URL with the
    largest area. Falls back to the plain src attribute if the JSON map is absent.
    """
    for selector in ["#landingImage", "#imgBlkFront", ".a-dynamic-image"]:
        img = soup.select_one(selector)
        if not img:
            continue
        dynamic = img.get("data-a-dynamic-image")
        if dynamic:
            try:
                url_map = json.loads(dynamic)
                if url_map:
                    return max(url_map, key=lambda u: url_map[u][0] * url_map[u][1])
            except Exception:
                pass
        src = img.get("src", "")
        if src and src.startswith("http"):
            return src
    return None


def _extract_specifications(soup: BeautifulSoup) -> dict[str, str]:
    """Extract key-value specifications from the product details tables."""
    specs: dict[str, str] = {}

    # Layout 1: technical specifications table
    for table_sel in [
        "#productDetails_techSpec_section_1",
        "#productDetails_techSpec_section_2",
        "#prodDetails table",
    ]:
        table = soup.select_one(table_sel)
        if table:
            for row in table.select("tr"):
                cells = row.select("th, td")
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    val = cells[1].get_text(strip=True)
                    if key and val:
                        specs[key] = val

    # Layout 2: detail bullets list
    if not specs:
        container = soup.select_one("#detailBulletsWrapper_feature_div, #detailBullets_feature_div")
        if container:
            for item in container.select("li"):
                text = item.get_text(" ", strip=True)
                if ":" in text:
                    parts = text.split(":", 1)
                    key = parts[0].strip().lstrip("‏‎")
                    val = parts[1].strip()
                    if key and val:
                        specs[key] = val

    return specs
