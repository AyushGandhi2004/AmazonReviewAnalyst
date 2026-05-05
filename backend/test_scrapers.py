"""Phase 2 scraper test — run this directly to verify both scrapers work.

Usage (from backend/ directory):
    python test_scrapers.py B08N5WRWNW
    python test_scrapers.py B08N5WRWNW --reviews-only
    python test_scrapers.py B08N5WRWNW --listing-only

Requires a valid .env file with SCRAPINGBEE_API_KEY and APIFY_API_TOKEN.
"""

import argparse
import asyncio
import json
import sys

sys.path.insert(0, ".")


async def test_listing_scraper(asin: str) -> None:
    """Run the listing scraper and print the result."""
    from scraper.listing_scraper import scrape_product_listing

    print(f"\n{'='*60}")
    print(f"LISTING SCRAPER — ASIN: {asin}")
    print("="*60)
    print("Calling ScrapingBee...")

    metadata = await scrape_product_listing(asin)
    result = metadata.model_dump()

    print(f"\nTitle:         {result['title']}")
    print(f"Price:         {result['price']}")
    print(f"Star Rating:   {result['star_rating']}")
    print(f"Total Reviews: {result['total_reviews']}")
    print(f"BSR:           {result['bsr']}")
    print(f"Bullet Points: {len(result['bullet_points'])} found")
    for bp in result["bullet_points"][:3]:
        print(f"  • {bp[:80]}")
    print(f"Specifications: {len(result['specifications'])} found")
    for k, v in list(result["specifications"].items())[:3]:
        print(f"  {k}: {v[:60]}")

    missing = [k for k, v in result.items() if v is None and k != "currency"]
    if missing:
        print(f"\nFields not extracted: {missing}")
    else:
        print("\nAll fields extracted successfully.")

    print("\nFull JSON output:")
    print(json.dumps(result, indent=2, default=str))


async def test_review_scraper(asin: str) -> None:
    """Run the review scraper and print the result summary."""
    from scraper.review_scraper import scrape_reviews

    print(f"\n{'='*60}")
    print(f"REVIEW SCRAPER — ASIN: {asin}")
    print("="*60)
    print("Calling Apify (this may take 1-3 minutes)...")

    reviews = await scrape_reviews(asin, max_reviews=100)

    print(f"\nTotal reviews retrieved: {len(reviews)}")

    if not reviews:
        print("ERROR: No reviews returned.")
        return

    ratings = [r.rating for r in reviews]
    print(f"Rating distribution:")
    for star in range(5, 0, -1):
        count = ratings.count(star)
        bar = "█" * count
        print(f"  {star}★  {count:3d}  {bar[:40]}")

    verified_count = sum(1 for r in reviews if r.verified_purchase)
    print(f"\nVerified purchases: {verified_count}/{len(reviews)}")

    print("\nSample 5-star review:")
    five_star = next((r for r in reviews if r.rating == 5), None)
    if five_star:
        print(f"  Title: {five_star.title}")
        print(f"  Date:  {five_star.date}")
        print(f"  Text:  {five_star.text[:200]}")

    print("\nSample 1-star review:")
    one_star = next((r for r in reviews if r.rating == 1), None)
    if one_star:
        print(f"  Title: {one_star.title}")
        print(f"  Date:  {one_star.date}")
        print(f"  Text:  {one_star.text[:200]}")
    else:
        print("  (no 1-star reviews in sample)")

    print(f"\nFull JSON for first review:")
    print(json.dumps(reviews[0].model_dump(), indent=2, default=str))


async def main() -> None:
    """Parse args and run the requested scraper tests."""
    parser = argparse.ArgumentParser(description="Test Phase 2 scrapers")
    parser.add_argument("asin", help="Amazon ASIN to test with (e.g. B08N5WRWNW)")
    parser.add_argument("--listing-only", action="store_true", help="Only run listing scraper")
    parser.add_argument("--reviews-only", action="store_true", help="Only run review scraper")
    args = parser.parse_args()

    asin = args.asin.strip().upper()

    run_listing = not args.reviews_only
    run_reviews = not args.listing_only

    if run_listing:
        try:
            await test_listing_scraper(asin)
        except Exception as exc:
            print(f"\nLISTING SCRAPER FAILED: {exc}")

    if run_reviews:
        try:
            await test_review_scraper(asin)
        except Exception as exc:
            print(f"\nREVIEW SCRAPER FAILED: {exc}")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
