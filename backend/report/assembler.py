"""Assembles all pipeline outputs into a FullReport."""

import logging
from typing import Any

from models import (
    ComparisonResult,
    CompetitorAdvantage,
    FullReport,
    ProductMetadata,
    ProductSummary,
    Recommendation,
    RecommendationsResult,
    ReportSection1,
    ReportSection2,
    ReportSection3,
    ReportSection4,
    ReportSection5,
    Review,
    ReviewSample,
    ReviewSamples,
    ComparisonRow,
)

logger = logging.getLogger(__name__)

# Max review samples per star-bucket per product included in the report
_SAMPLE_COUNT = 3


def assemble_report(
    run_id: str,
    your_asin: str,
    competitor_asins: list[str],
    metadata_list: list[ProductMetadata],
    reviews_by_asin: dict[str, list[Review]],
    summaries: list[dict],
    comparison: dict,
    comparison_table: dict | None,
    recommendations: dict,
) -> FullReport:
    """Combine all pipeline outputs into a single serialisable FullReport.

    Args:
        run_id: Unique identifier for this analysis run.
        your_asin: The seller's own product ASIN.
        competitor_asins: Competitor ASINs (may be empty).
        metadata_list: Scraped ProductMetadata objects for all products,
            in the same order as [your_asin] + competitor_asins.
        reviews_by_asin: Map of ASIN → list of Review objects.
        summaries: List of per-product LLM summary dicts, each already
            containing 'asin' and 'product_title' keys alongside the LLM
            output keys (strengths, weaknesses, top_complaints, top_praises,
            overall_reaction).
        comparison: LLM Call 2 output dict (your_product_advantages,
            competitor_advantages, market_gaps, overall_ranking).
        recommendations: LLM Call 3 output dict with key 'recommendations'.

    Returns:
        A fully populated FullReport ready to serialise and return via the API.
    """
    # Build a title lookup so section helpers can resolve ASIN → product name
    title_by_asin: dict[str, str] = {
        m.asin: (m.title or m.asin) for m in metadata_list
    }

    return FullReport(
        run_id=run_id,
        your_asin=your_asin,
        competitor_asins=competitor_asins,
        section_1=_build_section_1(metadata_list),
        section_2=_build_section_2(summaries),
        section_3=_build_section_3(comparison, comparison_table, title_by_asin),
        section_4=_build_section_4(recommendations),
        section_5=_build_section_5(reviews_by_asin, title_by_asin),
    )


# ─────────────────────────────────────────────
# Section builders
# ─────────────────────────────────────────────

def _build_section_1(metadata_list: list[ProductMetadata]) -> ReportSection1:
    """Section 1 — scraped metadata for all products side by side."""
    return ReportSection1(products=metadata_list)


def _build_section_2(summaries: list[dict]) -> ReportSection2:
    """Section 2 — per-product AI summaries from LLM Call 1."""
    product_summaries: list[ProductSummary] = []

    for raw in summaries:
        try:
            product_summaries.append(
                ProductSummary(
                    asin=raw.get("asin", ""),
                    product_title=raw.get("product_title", "Unknown"),
                    strengths=_as_str_list(raw.get("strengths")),
                    weaknesses=_as_str_list(raw.get("weaknesses")),
                    top_complaints=_top_freq_text(raw.get("top_complaints"), "complaint"),
                    top_praises=_top_freq_text(raw.get("top_praises"), "praise"),
                    overall_reaction=raw.get("overall_reaction"),
                )
            )
        except Exception as exc:
            logger.warning("Could not build ProductSummary from %s: %s", raw, exc)

    return ReportSection2(summaries=product_summaries)


def _build_section_3(
    comparison: dict,
    comparison_table: dict | None,
    title_by_asin: dict[str, str],
) -> ReportSection3:
    """Section 3 — cross-product comparison from LLM Call 2."""
    competitor_advantages: list[CompetitorAdvantage] = []

    raw_comps = comparison.get("competitor_advantages") or []
    if isinstance(raw_comps, list):
        for item in raw_comps:
            if not isinstance(item, dict):
                continue
            asin = item.get("asin", "")
            try:
                competitor_advantages.append(
                    CompetitorAdvantage(
                        asin=asin,
                        product_title=item.get("product_title") or title_by_asin.get(asin, asin),
                        advantages=_as_str_list(item.get("advantages")),
                    )
                )
            except Exception as exc:
                logger.warning("Could not build CompetitorAdvantage from %s: %s", item, exc)

    result = ComparisonResult(
        your_product_advantages=_as_str_list(comparison.get("your_product_advantages")),
        competitor_advantages=competitor_advantages,
        market_gaps=_as_str_list(comparison.get("market_gaps")),
        overall_ranking=_as_str_list(comparison.get("overall_ranking")),
    )
    # Build comparison_table rows if present — expect a list of objects
    rows: list[ComparisonRow] = []
    raw_table = None
    if comparison_table and isinstance(comparison_table, dict):
        raw_table = comparison_table.get("comparison_table")
    elif comparison and isinstance(comparison, dict):
        raw_table = comparison.get("comparison_table")

    if isinstance(raw_table, list):
        for item in raw_table:
            try:
                rows.append(
                    ComparisonRow(
                        property=str(item.get("property") or ""),
                        values={k: str(v) for k, v in (item.get("values") or {}).items()},
                    )
                )
            except Exception as exc:
                logger.warning("Could not parse comparison table row %s: %s", item, exc)

    return ReportSection3(comparison=result, comparison_table=rows)


def _build_section_4(recommendations: dict) -> ReportSection4:
    """Section 4 — seller recommendations from LLM Call 3."""
    recs: list[Recommendation] = []

    raw_list = recommendations.get("recommendations") or []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        try:
            priority = _normalise_enum(item.get("priority", "medium"), ("high", "medium", "low"), "medium")
            area = _normalise_enum(item.get("area", "product"), ("product", "listing", "pricing"), "product")
            recs.append(
                Recommendation(
                    priority=priority,
                    area=area,
                    action=str(item.get("action", "")),
                    rationale=str(item.get("rationale", "")),
                )
            )
        except Exception as exc:
            logger.warning("Could not build Recommendation from %s: %s", item, exc)

    # Sort high → medium → low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recs.sort(key=lambda r: priority_order.get(r.priority, 1))

    return ReportSection4(recommendations=RecommendationsResult(recommendations=recs))


def _build_section_5(
    reviews_by_asin: dict[str, list[Review]],
    title_by_asin: dict[str, str],
) -> ReportSection5:
    """Section 5 — curated review samples (top 3 five-star + top 3 one-star per product)."""
    all_samples: list[ReviewSamples] = []

    for asin, reviews in reviews_by_asin.items():
        five_star = [r for r in reviews if r.rating == 5][:_SAMPLE_COUNT]
        one_star  = [r for r in reviews if r.rating == 1][:_SAMPLE_COUNT]

        all_samples.append(
            ReviewSamples(
                asin=asin,
                product_title=title_by_asin.get(asin, asin),
                five_star=[_to_review_sample(r) for r in five_star],
                one_star=[_to_review_sample(r) for r in one_star],
            )
        )

    return ReportSection5(samples=all_samples)


# ─────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────

def _to_review_sample(review: Review) -> ReviewSample:
    """Convert a Review object to a ReviewSample."""
    return ReviewSample(
        rating=review.rating,
        title=review.title,
        text=review.text,
        date=review.date,
        verified_purchase=review.verified_purchase,
    )


def _top_freq_text(items: Any, text_key: str) -> list[str]:
    """Return a single-item list containing the text of the highest-frequency entry.

    Expects a list of dicts with `text_key` and a 'frequency' key (as returned
    by the LLM). Falls back to _as_str_list if the items are plain strings.
    """
    if not isinstance(items, list) or not items:
        return []
    dicts = [i for i in items if isinstance(i, dict)]
    if not dicts:
        return _as_str_list(items)

    def _freq(item: dict) -> int:
        try:
            return int(item.get("frequency", 0))
        except (ValueError, TypeError):
            return 0

    top = max(dicts, key=_freq)
    text = str(top.get(text_key, "")).strip()
    return [text] if text else []


def _as_str_list(value: Any) -> list[str]:
    """Coerce an LLM output field to a list of non-empty strings.

    Handles None, plain strings, and lists of mixed types gracefully.
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v).strip() for v in value if v and str(v).strip()]
    return [str(value)]


def _normalise_enum(value: Any, valid: tuple, default: str) -> str:
    """Return value lowercased if it is in valid, otherwise return default."""
    lowered = str(value).lower().strip()
    return lowered if lowered in valid else default
