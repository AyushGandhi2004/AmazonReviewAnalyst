"""Apify-based Amazon customer review scraper (junglee/amazon-reviews-scraper)."""

import asyncio
import logging
import re
from typing import Any, Optional

from apify_client import ApifyClient

from config import settings
from models import Review

logger = logging.getLogger(__name__)

AMAZON_PRODUCT_URL = "https://www.amazon.in/dp/{asin}"

# Apify actor run timeout: 10 minutes
ACTOR_TIMEOUT_SECS = 600


async def scrape_reviews(asin: str, max_reviews: int = 100) -> list[Review]:
    """Collect up to max_reviews customer reviews for a single ASIN via Apify.

    Runs the junglee/amazon-reviews-scraper Apify actor synchronously
    (wrapped in asyncio.to_thread), waits for SUCCEEDED status, then returns
    the dataset items as Review objects.

    Args:
        asin: The Amazon ASIN to collect reviews for.
        max_reviews: Maximum number of reviews to retrieve (default 100).

    Returns:
        A list of Review instances (may be fewer than max_reviews if the product
        has fewer published reviews).

    Raises:
        RuntimeError: If the Apify actor run fails or the dataset cannot be fetched.
        TimeoutError: If the actor run does not complete within ACTOR_TIMEOUT_SECS.
    """
    return await asyncio.to_thread(_run_apify_actor, asin, max_reviews)


def _run_apify_actor(asin: str, max_reviews: int) -> list[Review]:
    """Synchronous Apify actor execution — called via asyncio.to_thread.

    Args:
        asin: Amazon ASIN.
        max_reviews: Review count cap.

    Returns:
        Parsed list of Review objects.

    Raises:
        RuntimeError: On actor failure or bad status.
        TimeoutError: If the actor doesn't finish within the timeout.
    """
    client = ApifyClient(settings.apify_api_token)

    run_input = {
        "productUrls": [{"url": AMAZON_PRODUCT_URL.format(asin=asin)}],
        "maxReviews": max_reviews,
        "filterByRatings": ["allStars"],
    }

    logger.info("Starting Apify actor for ASIN %s (max %d reviews)", asin, max_reviews)

    try:
        run = client.actor(settings.apify_actor_id).call(
            run_input=run_input,
            timeout_secs=ACTOR_TIMEOUT_SECS,
        )
    except Exception as exc:
        raise RuntimeError(f"Apify actor call failed for ASIN {asin}: {exc}") from exc

    if run is None:
        raise RuntimeError(f"Apify returned no run object for ASIN {asin}.")

    status = run.get("status", "UNKNOWN")
    if status != "SUCCEEDED":
        raise RuntimeError(
            f"Apify actor finished with status '{status}' for ASIN {asin}. "
            f"Run ID: {run.get('id', 'unknown')}"
        )

    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        raise RuntimeError(f"Apify run for ASIN {asin} has no defaultDatasetId.")

    logger.info("Apify run SUCCEEDED for ASIN %s. Fetching dataset %s", asin, dataset_id)

    try:
        items = list(client.dataset(dataset_id).iterate_items())
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch Apify dataset {dataset_id}: {exc}") from exc

    reviews = [_parse_review_item(item, asin) for item in items]
    valid = [r for r in reviews if r is not None]

    logger.info("Parsed %d reviews for ASIN %s", len(valid), asin)
    return valid


def _parse_review_item(item: dict[str, Any], asin: str) -> Optional[Review]:
    """Normalise one junglee/amazon-reviews-scraper dataset item into a Review.

    Args:
        item: Raw dict from the Apify dataset.
        asin: ASIN to tag the review with.

    Returns:
        A Review instance, or None if the item lacks required fields.
    """
    try:
        # Skip rows that have no review content (e.g. foundNoReviews sentinel rows)
        if not item.get("reviewId"):
            return None

        rating = _extract_rating(item)
        text = _extract_text(item)

        if rating is None or text is None:
            logger.debug("Skipping review item missing rating or text: %s", list(item.keys()))
            return None

        return Review(
            asin=asin,
            rating=rating,
            text=text,
            title=_extract_field(item, ["reviewTitle", "title", "reviewHeadline", "headline"]),
            date=_extract_date(item),
            verified_purchase=_extract_verified(item),
        )
    except Exception as exc:
        logger.warning("Failed to parse review item: %s — %s", item, exc)
        return None


def _extract_rating(item: dict[str, Any]) -> Optional[int]:
    """Extract the numeric rating, handling int, float, or string variants."""
    # junglee actor returns "ratingScore" as a number
    raw = _extract_field(item, ["ratingScore", "rating", "reviewRating", "stars", "starRating", "score"])
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        val = int(raw)
        return val if 1 <= val <= 5 else None
    # Handle strings like "5.0 out of 5 stars" or "5"
    match = re.search(r"(\d+)", str(raw))
    if match:
        val = int(match.group(1))
        return val if 1 <= val <= 5 else None
    return None


def _extract_text(item: dict[str, Any]) -> Optional[str]:
    """Extract the review body text."""
    # junglee actor returns "reviewDescription" as the review body
    raw = _extract_field(item, ["reviewDescription", "reviewText", "text", "body", "reviewBody", "content", "reviewContent"])
    if raw is None:
        return None
    cleaned = str(raw).strip()
    return cleaned if cleaned else None


def _extract_date(item: dict[str, Any]) -> Optional[str]:
    """Extract the review date as a string."""
    # junglee actor returns "date"
    raw = _extract_field(item, ["date", "reviewDate", "publishedDate", "createdAt", "postedAt"])
    if raw is None:
        return None
    return str(raw).strip()


def _extract_verified(item: dict[str, Any]) -> bool:
    """Extract whether the purchase was verified."""
    # junglee actor returns "isVerified" as a boolean
    raw = _extract_field(item, ["isVerified", "verified", "verifiedPurchase", "isVerifiedPurchase"])
    if raw is None:
        return False
    if isinstance(raw, bool):
        return raw
    return str(raw).lower() in ("true", "yes", "1", "verified")


def _extract_field(item: dict[str, Any], keys: list[str]) -> Optional[Any]:
    """Return the first non-None value found under any of the given keys."""
    for key in keys:
        val = item.get(key)
        if val is not None:
            return val
    return None
