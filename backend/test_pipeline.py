"""Phase 5 integration test — verifies the full pipeline end-to-end.

Uses unittest.mock to stub the scrapers and LLM chains so the test runs
without any real API keys or network calls. ChromaDB and SentenceTransformer
run for real to exercise the actual embed/query path.

Usage (from backend/ directory):
    python -X utf8 test_pipeline.py
"""

import asyncio
import json
import os
import sys
import uuid
from unittest.mock import AsyncMock, patch

sys.path.insert(0, ".")
os.environ.setdefault("SCRAPINGBEE_API_KEY", "test")
os.environ.setdefault("APIFY_API_TOKEN", "test")
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("CHROMA_PERSIST_DIR", "./chroma_db_test")

from models import ProductMetadata, Review


# ─────────────────────────────────────────────
# Fixture data
# ─────────────────────────────────────────────

MOCK_METADATA = [
    ProductMetadata(
        asin="B0MYPRODUCT",
        title="SoundMax Pro X Wireless Headphones",
        price="$49.99",
        star_rating=3.8,
        total_reviews=2847,
        bsr="#342 in Headphones",
        bullet_points=["40-hour battery", "Active noise cancellation", "USB-C charging"],
    ),
    ProductMetadata(
        asin="B0COMPETITOR",
        title="AudioPeak Elite 500",
        price="$79.99",
        star_rating=4.4,
        total_reviews=5621,
        bsr="#87 in Headphones",
        bullet_points=["Premium build quality", "Multipoint Bluetooth", "30-hour battery"],
    ),
]

MOCK_REVIEWS_YOUR = [
    Review(asin="B0MYPRODUCT", rating=5, text="Amazing sound quality, bass is incredible.", verified_purchase=True),
    Review(asin="B0MYPRODUCT", rating=5, text="Battery lasts forever, very comfortable.", verified_purchase=True),
    Review(asin="B0MYPRODUCT", rating=2, text="Bluetooth keeps dropping, very frustrating.", verified_purchase=True),
    Review(asin="B0MYPRODUCT", rating=1, text="Headband cracked after 2 months. Terrible build.", verified_purchase=True),
    Review(asin="B0MYPRODUCT", rating=3, text="Good sound but microphone is poor for calls.", verified_purchase=False),
]

MOCK_REVIEWS_COMP = [
    Review(asin="B0COMPETITOR", rating=5, text="Premium build quality, feels very durable.", verified_purchase=True),
    Review(asin="B0COMPETITOR", rating=5, text="Multipoint Bluetooth is flawless.", verified_purchase=True),
    Review(asin="B0COMPETITOR", rating=2, text="Battery only lasts 20 hours, disappointing.", verified_purchase=True),
]

MOCK_SUMMARY_YOUR = {
    "asin": "B0MYPRODUCT",
    "product_title": "SoundMax Pro X Wireless Headphones",
    "strengths": ["Excellent sound quality", "Long battery life", "Comfortable fit"],
    "weaknesses": ["Poor build quality", "Bluetooth instability", "Weak microphone"],
    "top_complaints": ["Bluetooth drops frequently", "Headband cracks", "Mic is muffled"],
    "top_praises": ["Amazing bass response", "40-hour battery", "Comfortable for long use"],
    "overall_reaction": "Customers love the audio quality but are frustrated by reliability issues.",
}

MOCK_SUMMARY_COMP = {
    "asin": "B0COMPETITOR",
    "product_title": "AudioPeak Elite 500",
    "strengths": ["Premium build quality", "Reliable Bluetooth", "Great microphone"],
    "weaknesses": ["Shorter battery life", "Higher price", "No ANC"],
    "top_complaints": ["Battery life is only 20 hours", "Expensive ear pad replacements"],
    "top_praises": ["Rock-solid build", "Perfect multipoint Bluetooth", "Crystal clear mic"],
    "overall_reaction": "Customers value the premium construction and reliable connectivity.",
}

MOCK_COMPARISON = {
    "your_product_advantages": ["Lower price at $49.99", "Longer 40-hour battery", "Active noise cancellation"],
    "competitor_advantages": [
        {
            "asin": "B0COMPETITOR",
            "product_title": "AudioPeak Elite 500",
            "advantages": ["Superior build quality", "Better Bluetooth stability", "Clearer microphone"],
        }
    ],
    "market_gaps": ["No product offers both long battery AND premium build", "ANC quality varies widely"],
    "overall_ranking": [
        "1. AudioPeak Elite 500 — best overall reliability and build",
        "2. SoundMax Pro X — best value, best battery, but reliability issues",
    ],
}

MOCK_RECOMMENDATIONS = {
    "recommendations": [
        {"priority": "high", "area": "product", "action": "Redesign headband hinge with metal reinforcement.", "rationale": "Multiple reviews report headband cracking after 2 months."},
        {"priority": "high", "area": "product", "action": "Replace Bluetooth module with CSR8675 chipset.", "rationale": "Frequent disconnections are the top complaint; a better chipset resolves this."},
        {"priority": "medium", "area": "listing", "action": "Highlight 40-hour battery prominently in title.", "rationale": "Battery life is a top praise but not clear in current listing."},
        {"priority": "medium", "area": "product", "action": "Upgrade microphone to a dual-mic array.", "rationale": "Call quality complaints are the third most common issue."},
        {"priority": "low", "area": "pricing", "action": "Consider a $54.99 price point with upgraded materials.", "rationale": "A small price increase could fund quality improvements without losing value positioning."},
    ]
}


# ─────────────────────────────────────────────
# Test
# ─────────────────────────────────────────────

def sep(title: str = "") -> None:
    width = 65
    if title:
        pad = max(1, (width - len(title) - 2) // 2)
        print("-" * pad + f" {title} " + "-" * pad)
    else:
        print("-" * width)


async def run_mocked_pipeline() -> None:
    """Run the full pipeline with all external calls mocked."""
    from main import run_analysis_pipeline, _runs, RunState

    run_id = str(uuid.uuid4())
    _runs[run_id] = RunState(
        your_asin="B0MYPRODUCT",
        competitor_asins=["B0COMPETITOR"],
    )

    sep("PHASE 5 - PIPELINE INTEGRATION TEST")
    print(f"run_id : {run_id[:8]}...")
    print(f"ASINs  : B0MYPRODUCT, B0COMPETITOR")
    print()

    # Pre-import every module that patch() will target so their submodule
    # attributes are registered in sys.modules (required by Python 3.11 mock).
    import scraper.listing_scraper   # noqa: F401
    import scraper.review_scraper    # noqa: F401
    import pipeline.llm_chain        # noqa: F401

    with (
        patch("scraper.listing_scraper.scrape_product_listing",
              side_effect=AsyncMock(side_effect=lambda a: next(
                  m for m in MOCK_METADATA if m.asin == a
              ))),
        patch("scraper.review_scraper.scrape_reviews",
              side_effect=AsyncMock(side_effect=lambda a, _max: (
                  MOCK_REVIEWS_YOUR if a == "B0MYPRODUCT" else MOCK_REVIEWS_COMP
              ))),
        patch("pipeline.llm_chain.run_product_summary_chain",
              side_effect=lambda title, ctx: (
                  {k: v for k, v in MOCK_SUMMARY_YOUR.items()}
                  if "SoundMax" in title
                  else {k: v for k, v in MOCK_SUMMARY_COMP.items()}
              )),
        patch("pipeline.llm_chain.run_comparison_chain",
              return_value=MOCK_COMPARISON),
        patch("pipeline.llm_chain.run_recommendations_chain",
              return_value=MOCK_RECOMMENDATIONS),
    ):
        sep("Running pipeline (embeddings + RAG are real)")
        print("Loading SentenceTransformer model and running ChromaDB...")
        await run_analysis_pipeline(run_id)

    state = _runs[run_id]

    sep("Pipeline result")
    print(f"Status : {state.status}")
    print()

    assert state.status == "done", f"Expected 'done', got '{state.status}'"
    assert state.report is not None, "Report is None after pipeline completed"

    report = state.report

    # ── Section 1: Metadata ───────────────────────────────────────────────────
    sep("Section 1 - Scraped Metadata")
    products = report.section_1.products
    print(f"Products: {len(products)}")
    for p in products:
        print(f"  {p.asin}: {p.title} | {p.price} | {p.star_rating}* | {p.total_reviews} reviews")
    assert len(products) == 2, f"Expected 2 products, got {len(products)}"
    print("[PASS] Section 1")

    # ── Section 2: Summaries ─────────────────────────────────────────────────
    sep("Section 2 - AI Summaries")
    summaries = report.section_2.summaries
    print(f"Summaries: {len(summaries)}")
    for s in summaries:
        print(f"  {s.asin}: strengths={len(s.strengths)}, weaknesses={len(s.weaknesses)}")
        print(f"    Overall: {s.overall_reaction}")
    assert len(summaries) == 2
    assert all(s.strengths for s in summaries)
    assert all(s.weaknesses for s in summaries)
    print("[PASS] Section 2")

    # ── Section 3: Comparison ─────────────────────────────────────────────────
    sep("Section 3 - Comparison")
    comp = report.section_3.comparison
    print(f"Your advantages : {len(comp.your_product_advantages)}")
    print(f"Market gaps     : {len(comp.market_gaps)}")
    print(f"Overall ranking : {len(comp.overall_ranking)} entries")
    for adv in comp.competitor_advantages:
        print(f"  Competitor {adv.asin}: {len(adv.advantages)} advantages")
    assert comp.your_product_advantages
    assert comp.market_gaps
    assert comp.overall_ranking
    print("[PASS] Section 3")

    # ── Section 4: Recommendations ───────────────────────────────────────────
    sep("Section 4 - Recommendations")
    recs = report.section_4.recommendations.recommendations
    print(f"Recommendations: {len(recs)}")
    for r in recs:
        print(f"  [{r.priority.upper()}] [{r.area}] {r.action[:70]}")
    assert len(recs) >= 5
    assert all(r.priority in ("high", "medium", "low") for r in recs)
    assert all(r.area in ("product", "listing", "pricing") for r in recs)
    # High priority should come first (assembler sorts them)
    priorities = [r.priority for r in recs]
    high_idx = [i for i, p in enumerate(priorities) if p == "high"]
    low_idx  = [i for i, p in enumerate(priorities) if p == "low"]
    if high_idx and low_idx:
        assert max(high_idx) < min(low_idx), "Recommendations not sorted by priority"
    print("[PASS] Section 4 (including priority sort)")

    # ── Section 5: Review samples ────────────────────────────────────────────
    sep("Section 5 - Review Samples")
    for samples in report.section_5.samples:
        print(f"  {samples.asin}: {len(samples.five_star)} x 5-star, {len(samples.one_star)} x 1-star")
    assert len(report.section_5.samples) == 2
    your_samples = next(s for s in report.section_5.samples if s.asin == "B0MYPRODUCT")
    assert your_samples.five_star, "No 5-star samples for your product"
    assert your_samples.one_star,  "No 1-star samples for your product"
    print("[PASS] Section 5")

    # ── SSE events were queued ────────────────────────────────────────────────
    sep("SSE event queue")
    events = []
    while not state.queue.empty():
        events.append(await state.queue.get())
    # The __done__ sentinel should be the last item
    done_events = [e for e in events if e.get("__done__")]
    prog_events = [e for e in events if "step" in e]
    print(f"Progress events : {len(prog_events)}")
    print(f"Done sentinel   : {len(done_events)}")
    assert done_events, "No __done__ sentinel found in queue"
    assert len(prog_events) >= 7, f"Expected >=7 progress events, got {len(prog_events)}"
    pcts = [e["progress_pct"] for e in prog_events]
    assert pcts == sorted(pcts), f"Progress percentages not monotonically increasing: {pcts}"
    print(f"Progress %: {pcts}")
    print("[PASS] SSE events ordered and complete")

    # ── Report round-trip JSON ────────────────────────────────────────────────
    sep("Report JSON round-trip")
    report_json = report.model_dump_json()
    reparsed = json.loads(report_json)
    assert reparsed["run_id"] == run_id
    assert reparsed["your_asin"] == "B0MYPRODUCT"
    size_kb = len(report_json) / 1024
    print(f"Report JSON size: {size_kb:.1f} KB")
    print("[PASS] Report serialises and round-trips correctly")

    sep()
    print("All Phase 5 integration checks PASSED.")
    print()

    # Cleanup
    import shutil, pathlib
    shutil.rmtree(pathlib.Path("./chroma_db_test"), ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(run_mocked_pipeline())
