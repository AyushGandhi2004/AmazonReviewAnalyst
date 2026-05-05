"""Phase 3 RAG pipeline test — run this directly to verify embeddings and retrieval.

Usage (from backend/ directory):
    python test_rag.py

No API keys required. Uses a temporary ChromaDB collection that is cleaned up
after the test. The SentenceTransformer model (~90 MB) is downloaded from
HuggingFace Hub on first run and cached locally.
"""

import sys
import uuid
import os

sys.path.insert(0, ".")

# Override chroma dir to a temp location so tests don't pollute the real DB
os.environ.setdefault("CHROMA_PERSIST_DIR", "./chroma_db_test")
os.environ.setdefault("SCRAPINGBEE_API_KEY", "test")
os.environ.setdefault("APIFY_API_TOKEN", "test")
os.environ.setdefault("GROQ_API_KEY", "test")

from models import Review
from pipeline.embeddings import embed_and_store_reviews, get_collection_name, delete_run_collections
from pipeline.rag import RAG_QUERIES, query_reviews, format_context_for_llm


# ─────────────────────────────────────────────
# Mock reviews — designed to have clear thematic clusters
# so RAG retrieval can be evaluated visually
# ─────────────────────────────────────────────

MOCK_REVIEWS = [
    # ── Positive: sound quality ───────────────────────────────────────────────
    Review(asin="B0TEST00001", rating=5, verified_purchase=True, date="2024-01-10",
           title="Amazing sound",
           text="The audio quality is incredible. Bass is deep and rich, treble is crisp and clear. "
                "I use these headphones for music production and they are absolutely perfect."),
    Review(asin="B0TEST00001", rating=5, verified_purchase=True, date="2024-01-15",
           title="Best sound I've heard",
           text="Outstanding sound quality. These headphones deliver studio-quality audio at a "
                "fraction of the price. The surround sound is immersive and the highs are pristine."),
    Review(asin="B0TEST00001", rating=5, verified_purchase=False, date="2024-01-20",
           title="Perfect audio",
           text="Love the sound reproduction. Every instrument is distinct and the soundstage is wide. "
                "I've tried many headphones in this price range and none come close to this audio quality."),

    # ── Positive: battery life ────────────────────────────────────────────────
    Review(asin="B0TEST00001", rating=5, verified_purchase=True, date="2024-01-22",
           title="Battery lasts forever",
           text="Charged these on Monday and still going strong on Friday. Battery life is exceptional. "
                "I use them for about 6 hours a day and only charge them twice a week."),
    Review(asin="B0TEST00001", rating=4, verified_purchase=True, date="2024-02-01",
           title="Great battery",
           text="Battery life lives up to the 40-hour claim. I commute and work out daily and "
                "the charge lasts well over a week with moderate use."),

    # ── Positive: comfort ─────────────────────────────────────────────────────
    Review(asin="B0TEST00001", rating=5, verified_purchase=True, date="2024-02-05",
           title="So comfortable",
           text="Wore these for an 8-hour workday and forgot I had them on. The ear cushions "
                "are incredibly soft and the clamping force is just right. No ear fatigue at all."),
    Review(asin="B0TEST00001", rating=5, verified_purchase=False, date="2024-02-10",
           title="Perfect for long sessions",
           text="The comfort level is unmatched. Memory foam ear pads and lightweight design "
                "make these ideal for long listening sessions. My ears never get hot or sore."),

    # ── Negative: build quality ───────────────────────────────────────────────
    Review(asin="B0TEST00001", rating=2, verified_purchase=True, date="2024-02-15",
           title="Feels cheap",
           text="The plastic construction feels very cheap and flimsy. The headband creaks when "
                "adjusted and I'm worried it will snap. For the price, the build quality is disappointing."),
    Review(asin="B0TEST00001", rating=1, verified_purchase=True, date="2024-02-20",
           title="Broke after 2 months",
           text="The headband cracked and snapped at the hinge. The build quality is terrible — "
                "thin cheap plastic that cannot withstand daily use. Very disappointed."),
    Review(asin="B0TEST00001", rating=2, verified_purchase=True, date="2024-03-01",
           title="Poor durability",
           text="The materials feel cheap and the build quality is questionable. The swivel joints "
                "are loose and the plastic housing on the earcup is already showing cracks."),

    # ── Negative: Bluetooth connectivity ─────────────────────────────────────
    Review(asin="B0TEST00001", rating=2, verified_purchase=True, date="2024-03-05",
           title="Constant Bluetooth drops",
           text="The Bluetooth connection is unreliable. It drops every 10 minutes and I have "
                "to re-pair the device. This is a serious issue that makes them unusable in meetings."),
    Review(asin="B0TEST00001", rating=1, verified_purchase=True, date="2024-03-10",
           title="Bluetooth keeps disconnecting",
           text="Terrible Bluetooth stability. The headphones disconnect randomly and the range "
                "is poor — only works within 5 feet. The connection cuts out when I put my phone in my pocket."),
    Review(asin="B0TEST00001", rating=2, verified_purchase=False, date="2024-03-15",
           title="Connectivity issues",
           text="The wireless connection is inconsistent. Bluetooth keeps dropping and sometimes "
                "the headphones won't reconnect without a full power cycle. Very frustrating."),

    # ── Negative: call quality / microphone ──────────────────────────────────
    Review(asin="B0TEST00001", rating=2, verified_purchase=True, date="2024-03-20",
           title="Microphone is terrible",
           text="The microphone quality is awful for calls. Everyone on calls says I sound "
                "muffled and distant. The noise cancellation on the mic picks up everything except my voice."),
    Review(asin="B0TEST00001", rating=3, verified_purchase=True, date="2024-03-25",
           title="Good headphones but bad mic",
           text="Sound for music is great but the microphone is the weak link. Call quality "
                "is poor and colleagues constantly ask me to repeat myself. The mic needs improvement."),

    # ── Improvement suggestions ───────────────────────────────────────────────
    Review(asin="B0TEST00001", rating=3, verified_purchase=True, date="2024-04-01",
           title="Would love better ANC",
           text="Sound quality is good but the active noise cancellation could be much stronger. "
                "I would happily pay more for better noise cancellation. "
                "The ANC barely blocks office noise and doesn't work well on planes."),
    Review(asin="B0TEST00001", rating=3, verified_purchase=True, date="2024-04-05",
           title="Needs a better carrying case",
           text="The headphones are good but the included hard case is bulky and doesn't fit "
                "in a backpack easily. A slimmer folding design with a softer case would make "
                "these much more portable. Please improve the travel case."),
    Review(asin="B0TEST00001", rating=4, verified_purchase=True, date="2024-04-10",
           title="Great but upgrade the app",
           text="The companion app needs a major update. EQ settings are limited, the interface "
                "is clunky, and it crashes frequently. If the app were better these would be perfect. "
                "I'd love to see more customisation options added."),
    Review(asin="B0TEST00001", rating=3, verified_purchase=False, date="2024-04-15",
           title="Need multipoint Bluetooth",
           text="The biggest improvement would be adding multipoint Bluetooth connectivity to "
                "connect two devices simultaneously. Having to manually switch between my phone "
                "and laptop is inconvenient. This is a must-have feature competitors offer."),
    Review(asin="B0TEST00001", rating=4, verified_purchase=True, date="2024-04-20",
           title="Improve the microphone",
           text="Everything is excellent except the microphone. Please upgrade the mic for the "
                "next version — it is the single biggest weakness. Better mic and this would be a 5-star product."),
]


# ─────────────────────────────────────────────
# Test runner
# ─────────────────────────────────────────────

def print_separator(title: str = "") -> None:
    """Print a visual separator line."""
    width = 65
    if title:
        pad = max(1, (width - len(title) - 2) // 2)
        print("-" * pad + f" {title} " + "-" * pad)
    else:
        print("-" * width)


def run_test() -> None:
    """Embed mock reviews, run all 4 RAG queries, and print results."""
    run_id = str(uuid.uuid4())[:8]   # short ID for readability
    asin = "B0TEST00001"

    print_separator("PHASE 3 - RAG PIPELINE TEST")
    print(f"Run ID : {run_id}")
    print(f"ASIN   : {asin}")
    print(f"Reviews: {len(MOCK_REVIEWS)}")
    print()

    # ── Step 1: Embed and store ───────────────────────────────────────────────
    print_separator("Step 1: Embed and Store")
    print("Loading SentenceTransformer model (downloads ~90 MB on first run)...")

    collection_name = embed_and_store_reviews(run_id, asin, MOCK_REVIEWS)
    print(f"Collection created: '{collection_name}'")
    print()

    # ── Step 2: Run all 4 RAG queries ────────────────────────────────────────
    print_separator("Step 2: RAG Queries")
    rag_context = query_reviews(run_id, asin, top_k=5)

    for query, chunks in rag_context.items():
        print_separator(f"Query: {query!r}")
        if not chunks:
            print("  (no results)")
        else:
            for i, chunk in enumerate(chunks, 1):
                preview = chunk[:120].replace("\n", " ")
                print(f"  [{i}] {preview}{'...' if len(chunk) > 120 else ''}")
        print()

    # ── Step 3: Verify semantic relevance ────────────────────────────────────
    print_separator("Step 3: Semantic Relevance Check")

    complaints_chunks = " ".join(rag_context.get("what do customers complain about most", []))
    praises_chunks    = " ".join(rag_context.get("what do customers love and praise", []))
    suggestions_chunks = " ".join(rag_context.get("what specific product improvements do customers suggest", []))
    low_rating_chunks  = " ".join(rag_context.get("what are the most common reasons for low ratings", []))

    # Complaints should mention build quality, Bluetooth, or microphone
    complaint_keywords = ["cheap", "plastic", "crack", "bluetooth", "disconnect", "microphone", "terrible", "poor"]
    complaint_hits = [kw for kw in complaint_keywords if kw.lower() in complaints_chunks.lower()]

    # Praises should mention sound, battery, or comfort
    praise_keywords = ["sound", "audio", "battery", "comfortable", "quality", "incredible", "perfect"]
    praise_hits = [kw for kw in praise_keywords if kw.lower() in praises_chunks.lower()]

    # Suggestions should mention improvements
    suggestion_keywords = ["improve", "upgrade", "better", "add", "need", "would love", "multipoint", "case"]
    suggestion_hits = [kw for kw in suggestion_keywords if kw.lower() in suggestions_chunks.lower()]

    # Low rating should pull 1-2 star content
    low_rating_keywords = ["broke", "snap", "disconnect", "terrible", "awful", "cheap", "crack", "poor"]
    low_rating_hits = [kw for kw in low_rating_keywords if kw.lower() in low_rating_chunks.lower()]

    checks = [
        ("Complaints query returns complaint content",   len(complaint_hits) >= 2,   f"matched: {complaint_hits}"),
        ("Praises query returns praise content",          len(praise_hits) >= 2,      f"matched: {praise_hits}"),
        ("Suggestions query returns improvement content", len(suggestion_hits) >= 2,  f"matched: {suggestion_hits}"),
        ("Low-ratings query returns negative content",    len(low_rating_hits) >= 2,  f"matched: {low_rating_hits}"),
    ]

    all_passed = True
    for label, passed, detail in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {label}")
        print(f"         {detail}")
        if not passed:
            all_passed = False

    print()

    # ── Step 4: format_context_for_llm ───────────────────────────────────────
    print_separator("Step 4: format_context_for_llm")
    formatted = format_context_for_llm(rag_context)
    print(formatted[:600])
    if len(formatted) > 600:
        print("... (truncated)")
    print()

    # ── Cleanup ───────────────────────────────────────────────────────────────
    delete_run_collections(run_id, [asin])
    print_separator()
    if all_passed:
        print("All checks PASSED — Phase 3 RAG pipeline is working correctly.")
    else:
        print("Some checks FAILED — review the query results above.")
    print()


if __name__ == "__main__":
    run_test()
