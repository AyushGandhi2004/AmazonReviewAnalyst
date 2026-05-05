"""Pydantic models for all API request/response schemas and internal data structures."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────
# Request / Response — API layer
# ─────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    """Body for POST /api/analyze."""

    your_asin: str = Field(..., description="ASIN of the seller's own product")
    competitor_asins: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Up to 3 competitor ASINs",
    )

    @field_validator("your_asin", mode="before")
    @classmethod
    def strip_your_asin(cls, v: str) -> str:
        """Strip whitespace from the primary ASIN."""
        return v.strip().upper()

    @field_validator("competitor_asins", mode="before")
    @classmethod
    def strip_competitor_asins(cls, v: list[str]) -> list[str]:
        """Strip whitespace from all competitor ASINs."""
        return [a.strip().upper() for a in v]


class AnalyzeResponse(BaseModel):
    """Returned immediately from POST /api/analyze."""

    run_id: str = Field(..., description="UUID for this analysis run")


class ProgressEvent(BaseModel):
    """Shape of each SSE event emitted by GET /api/progress/{run_id}."""

    step: str = Field(..., description="Human-readable step name")
    status: Literal["running", "done", "error"] = "running"
    progress_pct: int = Field(..., ge=0, le=100, description="0-100 completion percentage")
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Response for GET /api/health."""

    status: Literal["ok"] = "ok"


# ─────────────────────────────────────────────
# Scraped product data
# ─────────────────────────────────────────────

class ProductMetadata(BaseModel):
    """Structured metadata scraped from an Amazon product listing."""

    asin: str
    title: Optional[str] = None
    price: Optional[str] = None          # raw string, e.g. "$29.99"
    currency: Optional[str] = None
    star_rating: Optional[float] = None  # e.g. 4.3
    total_reviews: Optional[int] = None
    bsr: Optional[str] = None            # e.g. "#1,234 in Electronics"
    bullet_points: list[str] = Field(default_factory=list)
    specifications: dict[str, str] = Field(default_factory=dict)
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────
# Review data
# ─────────────────────────────────────────────

class Review(BaseModel):
    """A single customer review from Apify."""

    asin: str
    rating: int = Field(..., ge=1, le=5)
    text: str
    date: Optional[str] = None
    verified_purchase: bool = False
    title: Optional[str] = None


class ReviewSample(BaseModel):
    """A curated review sample included in the report."""

    rating: int
    title: Optional[str] = None
    text: str
    date: Optional[str] = None
    verified_purchase: bool = False


# ─────────────────────────────────────────────
# LLM analysis outputs
# ─────────────────────────────────────────────

class ProductSummary(BaseModel):
    """Output from LLM Call 1 — per-product analysis."""

    asin: str
    product_title: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    top_complaints: list[str] = Field(default_factory=list)
    top_praises: list[str] = Field(default_factory=list)
    overall_reaction: Optional[str] = None


class CompetitorAdvantage(BaseModel):
    """Advantages one competitor has over the user's product."""

    asin: str
    product_title: str
    advantages: list[str] = Field(default_factory=list)


class ComparisonResult(BaseModel):
    """Output from LLM Call 2 — cross-product comparison."""

    your_product_advantages: list[str] = Field(default_factory=list)
    competitor_advantages: list[CompetitorAdvantage] = Field(default_factory=list)
    market_gaps: list[str] = Field(default_factory=list)
    overall_ranking: list[str] = Field(default_factory=list)


class ComparisonRow(BaseModel):
    """A single row in the comparison table: property + per-product short values."""

    property: str
    values: dict[str, str] = Field(default_factory=dict)


class Recommendation(BaseModel):
    """A single prioritized recommendation from LLM Call 3."""

    priority: Literal["high", "medium", "low"]
    area: Literal["product", "listing", "pricing"]
    action: str
    rationale: str


class RecommendationsResult(BaseModel):
    """Output from LLM Call 3 — seller recommendations."""

    recommendations: list[Recommendation] = Field(default_factory=list)


# ─────────────────────────────────────────────
# Full report
# ─────────────────────────────────────────────

class ReportSection1(BaseModel):
    """Scraped metadata for all products side by side."""

    products: list[ProductMetadata] = Field(default_factory=list)


class ReportSection2(BaseModel):
    """Per-product AI summaries."""

    summaries: list[ProductSummary] = Field(default_factory=list)


class ReportSection3(BaseModel):
    """Cross-product comparison."""

    comparison: ComparisonResult
    comparison_table: list[ComparisonRow] = Field(default_factory=list)


class ReportSection4(BaseModel):
    """Prioritized seller recommendations."""

    recommendations: RecommendationsResult


class ReviewSamples(BaseModel):
    """Best and worst review samples for one product."""

    asin: str
    product_title: str
    five_star: list[ReviewSample] = Field(default_factory=list)
    one_star: list[ReviewSample] = Field(default_factory=list)


class ReportSection5(BaseModel):
    """Raw review samples — top 3 five-star and one-star per product."""

    samples: list[ReviewSamples] = Field(default_factory=list)


class FullReport(BaseModel):
    """Complete analysis report returned by GET /api/report/{run_id}."""

    run_id: str
    your_asin: str
    competitor_asins: list[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    section_1: ReportSection1
    section_2: ReportSection2
    section_3: ReportSection3
    section_4: ReportSection4
    section_5: ReportSection5
