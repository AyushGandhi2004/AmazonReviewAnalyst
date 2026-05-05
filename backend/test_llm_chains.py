"""Phase 4 LLM chain test — run this directly to verify all 3 chains.

Usage (from backend/ directory):
    python test_llm_chains.py

Requires GROQ_API_KEY to be set in .env (or as an environment variable).
Each chain makes one real Groq API call; total cost is minimal (<1 cent).
"""

import json
import os
import sys

sys.path.insert(0, ".")

os.environ.setdefault("SCRAPINGBEE_API_KEY", "test")
os.environ.setdefault("APIFY_API_TOKEN", "test")


# ─────────────────────────────────────────────
# Mock data — realistic enough to get meaningful LLM output
# ─────────────────────────────────────────────

MOCK_PRODUCT_TITLE = "SoundMax Pro X Wireless Headphones"
MOCK_COMPETITOR_TITLE = "AudioPeak Elite 500 Headphones"

MOCK_REVIEW_CONTEXT = """\
[WHAT DO CUSTOMERS COMPLAIN ABOUT MOST]
- The plastic construction feels very cheap and flimsy. The headband creaks when adjusted.
- Bluetooth connection drops every 10 minutes, making them unusable in meetings.
- The headband cracked at the hinge after 2 months of daily use.
- Microphone quality is awful for calls. Everyone says I sound muffled and distant.
- Terrible Bluetooth stability. Disconnects randomly and range is only 5 feet.

[WHAT DO CUSTOMERS LOVE AND PRAISE]
- The audio quality is incredible. Bass is deep and rich, treble is crisp and clear.
- Outstanding sound quality for music production — studio-quality audio at low price.
- Battery life lives up to the 40-hour claim. Lasts well over a week with moderate use.
- Incredibly comfortable. Wore for 8-hour workday and forgot I had them on.
- Best sound I have heard at this price point. The surround sound is immersive.

[WHAT SPECIFIC PRODUCT IMPROVEMENTS DO CUSTOMERS SUGGEST]
- Active noise cancellation could be much stronger, barely blocks office noise.
- Needs multipoint Bluetooth to connect two devices simultaneously.
- The companion app needs a major update — EQ settings are limited and it crashes.
- A slimmer carrying case would make these much more portable for travel.
- Please upgrade the microphone for the next version; it is the single biggest weakness.

[WHAT ARE THE MOST COMMON REASONS FOR LOW RATINGS]
- Headband cracked and snapped at the hinge after 2 months — terrible build quality.
- Bluetooth keeps disconnecting; range is poor and requires re-pairing every session.
- Microphone is so bad that call participants ask you to repeat yourself constantly.
- Plastic housing on earcup is already showing cracks after light use.\
"""

MOCK_COMPETITOR_REVIEW_CONTEXT = """\
[WHAT DO CUSTOMERS COMPLAIN ABOUT MOST]
- Battery life is only 20 hours, significantly less than competitors.
- Ear cushions wear out quickly and replacements are expensive.
- No companion app for EQ customisation.

[WHAT DO CUSTOMERS LOVE AND PRAISE]
- Build quality is exceptional — feels premium and durable.
- Multipoint Bluetooth works flawlessly between phone and laptop.
- Microphone quality is excellent for calls and video meetings.

[WHAT SPECIFIC PRODUCT IMPROVEMENTS DO CUSTOMERS SUGGEST]
- Longer battery life is the most requested improvement.
- Cheaper replacement ear pads would be welcome.

[WHAT ARE THE MOST COMMON REASONS FOR LOW RATINGS]
- Battery life disappointment for the price.
- Ear pads degrade faster than expected.\
"""

MOCK_METADATA = [
    {
        "asin": "B0TEST00001",
        "title": MOCK_PRODUCT_TITLE,
        "price": "$49.99",
        "star_rating": 3.8,
        "total_reviews": 2847,
        "bsr": "#342 in Headphones",
    },
    {
        "asin": "B0COMP00001",
        "title": MOCK_COMPETITOR_TITLE,
        "price": "$79.99",
        "star_rating": 4.4,
        "total_reviews": 5621,
        "bsr": "#87 in Headphones",
    },
]


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def sep(title: str = "") -> None:
    """Print an ASCII separator line."""
    width = 65
    if title:
        pad = max(1, (width - len(title) - 2) // 2)
        print("-" * pad + f" {title} " + "-" * pad)
    else:
        print("-" * width)


def check_keys(result: dict, required: list[str], chain_name: str) -> bool:
    """Verify that all required keys are present and non-empty."""
    passed = True
    for key in required:
        val = result.get(key)
        present = val is not None and val != [] and val != ""
        status = "PASS" if present else "FAIL"
        print(f"  [{status}] '{key}' present and non-empty")
        if not present:
            passed = False
    return passed


def print_json(data: dict) -> None:
    """Pretty-print a dict as JSON (truncated at 1500 chars)."""
    s = json.dumps(data, indent=2)
    if len(s) > 1500:
        print(s[:1500] + "\n  ... (truncated)")
    else:
        print(s)


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────

def test_chain_1() -> dict:
    """Test LLM Call 1 — per-product summary."""
    from pipeline.llm_chain import run_product_summary_chain

    sep("Chain 1 - Product Summary")
    print(f"Product : {MOCK_PRODUCT_TITLE}")
    print("Calling Groq...")

    result = run_product_summary_chain(MOCK_PRODUCT_TITLE, MOCK_REVIEW_CONTEXT)

    print("\nResponse:")
    print_json(result)
    print("\nKey validation:")
    passed = check_keys(result, ["strengths", "weaknesses", "top_complaints", "top_praises", "overall_reaction"], "Chain 1")
    print(f"\nChain 1: {'PASS' if passed else 'FAIL'}")
    return result


def test_chain_2(summary_1: dict, summary_2: dict) -> dict:
    """Test LLM Call 2 — cross-product comparison."""
    from pipeline.llm_chain import run_comparison_chain, build_metadata_table

    sep("Chain 2 - Cross-product Comparison")
    print(f"Your product   : {MOCK_PRODUCT_TITLE}")
    print(f"Competitor     : {MOCK_COMPETITOR_TITLE}")
    print("Calling Groq...")

    all_summaries = json.dumps(
        {
            MOCK_METADATA[0]["asin"]: summary_1,
            MOCK_METADATA[1]["asin"]: summary_2,
        },
        indent=2,
    )
    metadata_table = build_metadata_table(MOCK_METADATA)

    result = run_comparison_chain(
        user_product_title=MOCK_PRODUCT_TITLE,
        all_summaries=all_summaries,
        metadata_table=metadata_table,
        num_products=2,
    )

    print("\nResponse:")
    print_json(result)
    print("\nKey validation:")
    passed = check_keys(
        result,
        ["your_product_advantages", "competitor_advantages", "market_gaps", "overall_ranking"],
        "Chain 2",
    )
    print(f"\nChain 2: {'PASS' if passed else 'FAIL'}")
    return result


def test_chain_3(comparison: dict) -> dict:
    """Test LLM Call 3 — seller recommendations."""
    from pipeline.llm_chain import run_recommendations_chain

    sep("Chain 3 - Seller Recommendations")
    print("Calling Groq...")

    result = run_recommendations_chain(json.dumps(comparison, indent=2))

    print("\nResponse:")
    print_json(result)

    recs = result.get("recommendations", [])
    print("\nKey validation:")
    has_recs = len(recs) >= 5
    print(f"  [{'PASS' if has_recs else 'FAIL'}] at least 5 recommendations returned (got {len(recs)})")

    valid_fields = all(
        all(k in r for k in ["priority", "area", "action", "rationale"])
        for r in recs
    )
    print(f"  [{'PASS' if valid_fields else 'FAIL'}] all recommendations have required fields")

    valid_priorities = all(r.get("priority") in ("high", "medium", "low") for r in recs)
    print(f"  [{'PASS' if valid_priorities else 'FAIL'}] all priorities are high/medium/low")

    valid_areas = all(r.get("area") in ("product", "listing", "pricing") for r in recs)
    print(f"  [{'PASS' if valid_areas else 'FAIL'}] all areas are product/listing/pricing")

    passed = has_recs and valid_fields and valid_priorities and valid_areas
    print(f"\nChain 3: {'PASS' if passed else 'FAIL'}")
    return result


def test_end_to_end(summary_1: dict, comparison: dict, recommendations: dict) -> None:
    """Verify the 3 chains wire together correctly end-to-end."""
    sep("End-to-end wiring check")

    # Chain 1 output feeds into Chain 2
    chain2_input_ok = bool(summary_1.get("strengths") or summary_1.get("weaknesses"))
    print(f"  [{'PASS' if chain2_input_ok else 'FAIL'}] Chain 1 output has content for Chain 2 input")

    # Chain 2 output feeds into Chain 3
    chain3_input_ok = bool(
        comparison.get("your_product_advantages") or comparison.get("market_gaps")
    )
    print(f"  [{'PASS' if chain3_input_ok else 'FAIL'}] Chain 2 output has content for Chain 3 input")

    # Chain 3 output has actionable content
    recs = recommendations.get("recommendations", [])
    high_priority = [r for r in recs if r.get("priority") == "high"]
    print(f"  [{'PASS' if high_priority else 'WARN'}] Chain 3 contains high-priority recommendations "
          f"(found {len(high_priority)})")

    print(f"\nAll 3 chains execute sequentially: PASS")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main() -> None:
    """Run all chain tests sequentially, passing outputs between them."""
    sep("PHASE 4 - LLM CHAIN TESTS")
    print("Model  :", end=" ")

    # Validate API key before running
    try:
        from config import settings
        model = settings.groq_model
        print(model)
    except Exception as exc:
        print(f"\nERROR: Could not load config: {exc}")
        print("Make sure GROQ_API_KEY is set in your .env file.")
        sys.exit(1)

    print()
    all_passed = True

    # ── Chain 1 (run for both products) ──────────────────────────────────────
    summary_1 = test_chain_1()
    print()

    # Run chain 1 for the competitor too (same function, different context)
    sep("Chain 1 - Product Summary (Competitor)")
    print(f"Product : {MOCK_COMPETITOR_TITLE}")
    print("Calling Groq...")
    from pipeline.llm_chain import run_product_summary_chain
    summary_2 = run_product_summary_chain(MOCK_COMPETITOR_TITLE, MOCK_COMPETITOR_REVIEW_CONTEXT)
    print("Competitor summary generated.")
    print()

    # ── Chain 2 ───────────────────────────────────────────────────────────────
    comparison = test_chain_2(summary_1, summary_2)
    print()

    # ── Chain 3 ───────────────────────────────────────────────────────────────
    recommendations = test_chain_3(comparison)
    print()

    # ── End-to-end wiring ─────────────────────────────────────────────────────
    test_end_to_end(summary_1, comparison, recommendations)
    print()

    sep()
    print("Phase 4 LLM chain tests complete.")
    print()


if __name__ == "__main__":
    main()
