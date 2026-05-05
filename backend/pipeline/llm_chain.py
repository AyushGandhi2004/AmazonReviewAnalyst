"""LangChain chains and Groq LLM calls for AI analysis.

All prompts are defined as named constants per the project spec.
Every LLM call demands JSON output and includes fallback JSON parsing.
"""

import json
import logging
import re
from typing import Optional

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Prompt constants (kept under 500 tokens each)
# ─────────────────────────────────────────────

PROMPT_PRODUCT_SUMMARY = """\
You are an expert Amazon product analyst.
Below are customer review excerpts for the product: {product_title}

Analyze these reviews and return a JSON object with exactly these keys:
  - strengths: list of 3-5 things customers consistently praise
  - weaknesses: list of 3-5 things customers consistently complain about
  - top_complaints: list of top 3 specific complaints with frequency signal
  - top_praises: list of top 3 specific praises with frequency signal
  - overall_reaction: one sentence summarising the overall customer sentiment

Review excerpts:
{review_context}

Return ONLY valid JSON, no explanation, no markdown.\
"""

PROMPT_COMPARISON = """\
You are an expert Amazon market analyst.
Below is a summary of {num_products} competing products.
Your product is: {user_product_title}

Product summaries:
{all_summaries}

Product metadata:
{metadata_table}

Return a JSON object with exactly these keys:
  - your_product_advantages: list of 3-5 clear advantages your product has
  - competitor_advantages: list where each item has "asin", "product_title", \
and "advantages" (list of strings)
  - market_gaps: list of 2-3 unmet needs none of the products fully address
  - overall_ranking: list ranking all products 1 to N; each entry is one sentence that MUST begin with the product ASIN in the format "ASIN B0XXXXXXXXXX is ranked Nth because ..."

Return ONLY valid JSON, no explanation, no markdown.\
"""

PROMPT_RECOMMENDATIONS = """\
You are a product consultant helping an Amazon seller improve their product and listing.

Based on this competitive analysis:
{comparison_json}

Generate 5-8 specific, prioritized recommendations.
Each must be actionable — not vague advice.
Focus on: product quality improvements, listing copy, pricing strategy, \
and addressing specific customer complaints.

Return a JSON object with key "recommendations", where each item has:
  - priority: exactly "high", "medium", or "low"
  - area: exactly "product", "listing", or "pricing"
  - action: one clear sentence describing what to DO
  - rationale: one sentence explaining WHY, citing evidence from the analysis

Return ONLY valid JSON, no explanation, no markdown.\
"""


PROMPT_COMPARISON_TABLE = """\
You are an expert Amazon product analyst.

Use the compact JSON payload below to build a comparison table. Extract only properties that are clearly supported by the data. Prefer specs and bullet points first, then review signals. If a product-value pair is missing or unclear, use "-".

Return a JSON object with a single key "comparison_table". The value must be a list of rows, each row shaped like:
    - property: string
    - values: object mapping ASIN -> short value string

Payload:
{comparison_payload}

Return ONLY valid JSON, no explanation, no markdown.\
"""


# ─────────────────────────────────────────────
# LLM singleton — loaded once, reused across all calls
# ─────────────────────────────────────────────

_llm: Optional[ChatGroq] = None


def _get_llm() -> ChatGroq:
    """Return the shared ChatGroq instance, initialising it on first call."""
    global _llm
    if _llm is None:
        logger.info("Initialising Groq LLM: %s", settings.groq_model)
        _llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
    return _llm


# ─────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────

def _build_prompt(template: str, **kwargs: str) -> str:
    """Substitute {key} placeholders in a prompt template via direct string replace.

    Uses str.replace instead of str.format so that values containing curly
    braces (e.g. JSON fragments inside review context) are never misinterpreted
    as additional template variables.
    """
    result = template
    for key, value in kwargs.items():
        result = result.replace("{" + key + "}", str(value))
    return result


def _safe_parse_json(raw: str, fallback: dict) -> dict:
    """Parse JSON from LLM output with multi-strategy fallback.

    Strategies tried in order:
    1. Direct JSON parse of the stripped response.
    2. Strip markdown code fences (```json ... ```) then parse.
    3. Regex-extract the first {...} block and parse that.
    4. Return the provided fallback dict and log a warning.
    """
    stripped = raw.strip()

    # Strategy 1 — direct parse
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Strategy 2 — strip code fences
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", stripped, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 3 — extract first JSON object
    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    logger.warning("LLM returned malformed JSON; using fallback. Raw output: %s", raw[:300])
    return fallback


def _compact_text(value: str | None, max_chars: int = 120) -> str:
    """Collapse whitespace and cap text length to keep LLM payloads small."""
    if not value:
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text[:max_chars]


def _compact_list(values: list | None, max_items: int = 4, max_chars: int = 120) -> list[str]:
    """Trim a list to a small number of short strings."""
    if not values:
        return []
    compacted: list[str] = []
    for value in values[:max_items]:
        text = _compact_text(str(value), max_chars=max_chars)
        if text:
            compacted.append(text)
    return compacted


def build_comparison_table_payload(
    metadata_list: list[dict],
    summaries: list[dict],
    rag_context_by_asin: dict[str, dict[str, list[str]]],
) -> str:
    """Build a compact JSON payload for the comparison-table LLM call.

    The payload intentionally keeps only a few short signals per product so the
    request stays well below model context limits.
    """
    summary_by_asin = {item.get("asin"): item for item in summaries}
    query_limit = 2
    chunk_limit = 2

    compact_products: list[dict] = []
    for meta in metadata_list:
        asin = str(meta.get("asin") or "")
        summary = summary_by_asin.get(asin, {})
        rag_context = rag_context_by_asin.get(asin) or {}

        compact_reviews: dict[str, list[str]] = {}
        for query, chunks in rag_context.items():
            compact_reviews[query] = [
                _compact_text(chunk, max_chars=120)
                for chunk in (chunks or [])[:chunk_limit]
                if _compact_text(chunk, max_chars=120)
            ]

        compact_products.append({
            "asin": asin,
            "title": _compact_text(meta.get("title") or asin, max_chars=80),
            "price": meta.get("price"),
            "rating": meta.get("star_rating"),
            "review_count": meta.get("total_reviews"),
            "bullet_points": _compact_list(meta.get("bullet_points"), max_items=4, max_chars=90),
            "specifications": {
                key: _compact_text(value, max_chars=80)
                for key, value in list((meta.get("specifications") or {}).items())[:6]
                if _compact_text(value, max_chars=80)
            },
            "summary_signals": {
                "strengths": _compact_list(summary.get("strengths"), max_items=2, max_chars=90),
                "weaknesses": _compact_list(summary.get("weaknesses"), max_items=2, max_chars=90),
                "top_complaints": _compact_list(summary.get("top_complaints"), max_items=2, max_chars=90),
                "top_praises": _compact_list(summary.get("top_praises"), max_items=2, max_chars=90),
            },
            "review_signals": {
                query: snippets[:query_limit]
                for query, snippets in compact_reviews.items()
                if snippets
            },
        })

    return json.dumps({"products": compact_products}, ensure_ascii=True, separators=(",", ":"))


def _invoke(prompt: str, fallback: dict) -> dict:
    """Send a prompt to Groq and return the parsed JSON response.

    Args:
        prompt: The fully-rendered prompt string.
        fallback: Dict returned if the response cannot be parsed as JSON.

    Returns:
        Parsed response dict.

    Raises:
        RuntimeError: If the Groq API call itself fails (network, auth, etc.).
    """
    llm = _get_llm()
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content
        logger.debug("Raw LLM response (%d chars): %s", len(raw), raw[:200])
        return _safe_parse_json(raw, fallback)
    except Exception as exc:
        raise RuntimeError(f"Groq API call failed: {exc}") from exc


# ─────────────────────────────────────────────
# Public chain functions
# ─────────────────────────────────────────────

def run_product_summary_chain(product_title: str, review_context: str) -> dict:
    """Call Groq to generate a per-product summary from review excerpts (LLM Call 1).

    Args:
        product_title: Display name of the product being analysed.
        review_context: Formatted review chunks from RAG retrieval
            (output of pipeline.rag.format_context_for_llm).

    Returns:
        Parsed dict with keys: strengths, weaknesses, top_complaints,
        top_praises, overall_reaction.

    Raises:
        RuntimeError: If the Groq API call fails.
    """
    prompt = _build_prompt(
        PROMPT_PRODUCT_SUMMARY,
        product_title=product_title,
        review_context=review_context,
    )
    fallback = {
        "strengths": [],
        "weaknesses": [],
        "top_complaints": [],
        "top_praises": [],
        "overall_reaction": "Analysis unavailable due to an error.",
    }
    logger.info("Running product summary chain for: %s", product_title)
    return _invoke(prompt, fallback)


def run_comparison_chain(
    user_product_title: str,
    all_summaries: str,
    metadata_table: str,
    num_products: int,
) -> dict:
    """Call Groq to generate a cross-product comparison (LLM Call 2).

    Args:
        user_product_title: Title of the seller's own product.
        all_summaries: JSON-serialised per-product summaries from Call 1.
        metadata_table: Human-readable table of scraped metadata (price, rating, BSR).
        num_products: Total number of products being compared.

    Returns:
        Parsed dict with keys: your_product_advantages, competitor_advantages,
        market_gaps, overall_ranking.

    Raises:
        RuntimeError: If the Groq API call fails.
    """
    prompt = _build_prompt(
        PROMPT_COMPARISON,
        user_product_title=user_product_title,
        all_summaries=all_summaries,
        metadata_table=metadata_table,
        num_products=str(num_products),
    )
    fallback = {
        "your_product_advantages": [],
        "competitor_advantages": [],
        "market_gaps": [],
        "overall_ranking": [],
    }
    logger.info("Running comparison chain for %d products (user: %s)", num_products, user_product_title)
    return _invoke(prompt, fallback)


def run_recommendations_chain(comparison_json: str) -> dict:
    """Call Groq to generate prioritised seller recommendations (LLM Call 3).

    Args:
        comparison_json: JSON string of the comparison output from Call 2.

    Returns:
        Parsed dict with key 'recommendations', each item having
        priority, area, action, rationale.

    Raises:
        RuntimeError: If the Groq API call fails.
    """
    prompt = _build_prompt(
        PROMPT_RECOMMENDATIONS,
        comparison_json=comparison_json,
    )
    fallback = {"recommendations": []}
    logger.info("Running recommendations chain.")
    return _invoke(prompt, fallback)


# ─────────────────────────────────────────────
# Formatting helpers used when building chain inputs
# ─────────────────────────────────────────────

def build_metadata_table(products: list[dict]) -> str:
    """Format a list of ProductMetadata dicts into a readable table string.

    Used to build the metadata_table argument for run_comparison_chain.

    Args:
        products: List of dicts with keys: asin, title, price, star_rating,
            total_reviews, bsr.

    Returns:
        A plain-text table string, one product per row.
    """
    header = f"{'ASIN':<12} {'Title':<40} {'Price':<10} {'Rating':<8} {'Reviews':<10} BSR"
    rows = [header, "-" * len(header)]
    for p in products:
        title = (p.get("title") or "N/A")[:38]
        rows.append(
            f"{p.get('asin', 'N/A'):<12} "
            f"{title:<40} "
            f"{p.get('price') or 'N/A':<10} "
            f"{p.get('star_rating') or 'N/A':<8} "
            f"{p.get('total_reviews') or 'N/A':<10} "
            f"{p.get('bsr') or 'N/A'}"
        )
    return "\n".join(rows)


def run_comparison_table_chain(
    comparison_payload: str,
) -> dict:
    """Call Groq to generate a compact comparison table mapping properties to per-product values."""
    prompt = _build_prompt(
        PROMPT_COMPARISON_TABLE,
        comparison_payload=comparison_payload,
    )
    fallback = {"comparison_table": []}
    logger.info("Running comparison table chain.")
    return _invoke(prompt, fallback)
