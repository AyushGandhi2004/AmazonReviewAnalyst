"""FastAPI application — all routes for the Amazon Review Analyzer.

Start with:
    uvicorn main:app --reload --port 8000

API docs available at: http://localhost:8000/docs
"""

import asyncio
import json
import logging
import sys
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sse_starlette.sse import EventSourceResponse

# Add backend/ to the path so relative imports work when running from backend/
sys.path.insert(0, ".")

from config import settings
from models import AnalyzeRequest, AnalyzeResponse, FullReport, HealthResponse
from utils.validators import validate_asins

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# In-memory run store
# ─────────────────────────────────────────────

class RunState:
    """Holds all mutable state for a single analysis run."""

    def __init__(self, your_asin: str, competitor_asins: list[str]) -> None:
        """Initialise run state with ASINs and an empty event queue."""
        self.your_asin = your_asin
        self.competitor_asins = competitor_asins
        self.status: str = "pending"   # pending | running | done | error
        self.report: FullReport | None = None
        self.queue: asyncio.Queue = asyncio.Queue()


# run_id → RunState
_runs: dict[str, RunState] = {}


# ─────────────────────────────────────────────
# Application lifecycle
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown hook."""
    logger.info("Amazon Review Analyzer API starting up.")
    yield
    logger.info("Amazon Review Analyzer API shutting down.")


# ─────────────────────────────────────────────
# App instance
# ─────────────────────────────────────────────

app = FastAPI(
    title="Amazon Review Analyzer",
    description="AI-powered competitive analysis of Amazon products using scraped reviews.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Background task — analysis pipeline
# ─────────────────────────────────────────────

async def _emit(state: RunState, step: str, status: str, pct: int, message: str | None = None) -> None:
    """Push a progress event onto the run's SSE queue."""
    await state.queue.put({
        "step": step,
        "status": status,
        "progress_pct": pct,
        "message": message,
    })


async def run_analysis_pipeline(run_id: str) -> None:
    """Execute the full 7-step analysis pipeline, emitting an SSE event after each step.

    All blocking I/O (scraping, embeddings, LLM calls) runs in a thread pool
    via asyncio.to_thread so the FastAPI event loop stays responsive.

    Steps:
        1  Input validated
        2  Product listings scraped  (ScrapingBee — parallel)
        3  Reviews collected         (Apify — sequential per rate-limit guidance)
        4  Reviews indexed           (SentenceTransformer + ChromaDB)
        5  Review insights extracted (RAG queries)
        6  AI analysis complete      (Groq LLM — 3 chained calls)
        7  Report assembled + ready
    """
    # Deferred imports keep server startup fast and avoid loading heavy ML
    # libraries (sentence-transformers, chromadb) until a run actually starts.
    from scraper.listing_scraper import scrape_product_listing
    from scraper.review_scraper import scrape_reviews
    from pipeline.embeddings import embed_and_store_reviews, delete_run_collections
    from pipeline.rag import query_reviews, format_context_for_llm
    from pipeline.llm_chain import (
        run_product_summary_chain,
        run_comparison_chain,
        run_comparison_table_chain,
        run_recommendations_chain,
        build_metadata_table,
        build_comparison_table_payload,
    )
    from report.assembler import assemble_report

    state = _runs[run_id]
    state.status = "running"
    all_asins = [state.your_asin] + state.competitor_asins

    try:
        # ── Step 1: Input validated ───────────────────────────────────────────
        await _emit(state, "Input validated", "done", 5)

        # ── Step 2: Scrape product listings (parallel) ────────────────────────
        await _emit(state, "Scraping product listings", "running", 10)
        metadata_list = list(
            await asyncio.gather(*[scrape_product_listing(asin) for asin in all_asins])
        )
        logger.info("Scraped metadata for %d products", len(metadata_list))
        await _emit(state, "Product data scraped", "done", 25)

        # ── Step 3: Collect reviews (sequential — Apify rate limits) ──────────
        await _emit(state, "Collecting reviews", "running", 30)
        reviews_by_asin: dict = {}
        for asin in all_asins:
            reviews_by_asin[asin] = await scrape_reviews(asin, settings.max_reviews_per_product)
            logger.info("Collected %d reviews for ASIN %s", len(reviews_by_asin[asin]), asin)
        await _emit(state, "Reviews collected", "done", 45)

        # ── Step 4: Embed and store in ChromaDB ───────────────────────────────
        await _emit(state, "Indexing reviews in vector store", "running", 50)
        for asin, reviews in reviews_by_asin.items():
            await asyncio.to_thread(embed_and_store_reviews, run_id, asin, reviews)
        await _emit(state, "Reviews indexed", "done", 60)

        # ── Step 5: RAG queries ───────────────────────────────────────────────
        await _emit(state, "Extracting review insights", "running", 65)
        rag_context_by_asin: dict = {}
        for asin in all_asins:
            if not reviews_by_asin.get(asin):
                logger.warning("Skipping RAG query for ASIN %s — no reviews collected.", asin)
                rag_context_by_asin[asin] = {}
            else:
                rag_context_by_asin[asin] = await asyncio.to_thread(query_reviews, run_id, asin)
        await _emit(state, "Review insights extracted", "done", 75)

        # ── Step 6: LLM analysis ──────────────────────────────────────────────
        await _emit(state, "Running AI analysis", "running", 80)

        # LLM Call 1 — per-product summaries
        summaries: list[dict] = []
        for meta in metadata_list:
            context = format_context_for_llm(rag_context_by_asin[meta.asin])
            product_title = meta.title or meta.asin
            raw = await asyncio.to_thread(run_product_summary_chain, product_title, context)
            raw["asin"] = meta.asin
            raw["product_title"] = product_title
            summaries.append(raw)
            logger.info("Summary generated for ASIN %s", meta.asin)

        # LLM Call 2 — cross-product comparison
        user_product_title = metadata_list[0].title or state.your_asin
        all_summaries_json = json.dumps(
            {s["asin"]: s for s in summaries}, indent=2
        )
        metadata_table = build_metadata_table(
            [m.model_dump() for m in metadata_list]
        )
        comparison = await asyncio.to_thread(
            run_comparison_chain,
            user_product_title,
            all_summaries_json,
            metadata_table,
            len(all_asins),
        )

        # LLM Call 2.5 — generate compact comparison table mapping properties -> per-product values
        per_product_contexts = {
            m.asin: format_context_for_llm(rag_context_by_asin.get(m.asin) or {})
            for m in metadata_list
        }
        comparison_table = await asyncio.to_thread(
            run_comparison_table_chain,
            build_comparison_table_payload(
                [m.model_dump() for m in metadata_list],
                summaries,
                rag_context_by_asin,
            ),
        )

        # LLM Call 3 — seller recommendations
        recommendations = await asyncio.to_thread(
            run_recommendations_chain,
            json.dumps(comparison),
        )

        await _emit(state, "AI analysis complete", "done", 90)

        # ── Step 7: Assemble report ───────────────────────────────────────────
        await _emit(state, "Assembling report", "running", 95)
        state.report = assemble_report(
            run_id=run_id,
            your_asin=state.your_asin,
            competitor_asins=state.competitor_asins,
            metadata_list=metadata_list,
            reviews_by_asin=reviews_by_asin,
            summaries=summaries,
            comparison=comparison,
            comparison_table=comparison_table,
            recommendations=recommendations,
        )
        await _emit(state, "Report ready", "done", 100)

        state.status = "done"
        await state.queue.put({"__done__": True})

    except Exception as exc:
        logger.exception("Pipeline failed for run %s", run_id)
        state.status = "error"
        await state.queue.put({
            "step": "Pipeline error",
            "status": "error",
            "progress_pct": 0,
            "message": str(exc),
        })
        await state.queue.put({"__done__": True})
    finally:
        # Clean up ChromaDB collections for this run to free disk space
        try:
            from pipeline.embeddings import delete_run_collections
            delete_run_collections(run_id, all_asins)
        except Exception:
            pass  # cleanup failure must never mask the pipeline result


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Liveness probe — returns ok if the server is running."""
    return HealthResponse()


@app.post("/api/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
async def start_analysis(
    body: AnalyzeRequest,
    background_tasks: BackgroundTasks,
) -> AnalyzeResponse:
    """Accept ASINs, validate them, and kick off the analysis pipeline.

    Returns a run_id immediately. Use GET /api/progress/{run_id} to
    stream live progress via SSE, and GET /api/report/{run_id} to fetch
    the completed report.
    """
    # Validate ASIN formats
    errors = validate_asins(body.your_asin, body.competitor_asins)
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    run_id = str(uuid.uuid4())
    _runs[run_id] = RunState(
        your_asin=body.your_asin,
        competitor_asins=body.competitor_asins,
    )

    background_tasks.add_task(run_analysis_pipeline, run_id)
    logger.info("Analysis started: run_id=%s asins=%s", run_id, [body.your_asin] + body.competitor_asins)

    return AnalyzeResponse(run_id=run_id)


@app.get("/api/progress/{run_id}", tags=["Analysis"])
async def stream_progress(run_id: str) -> EventSourceResponse:
    """Stream live analysis progress as Server-Sent Events.

    Each event has the shape:
        { "step": "...", "status": "running|done|error",
          "progress_pct": 0-100, "message": "..." }

    A final event of type 'analysis_done' is emitted when the full report
    is ready.
    """
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    state = _runs[run_id]

    async def event_generator() -> AsyncGenerator[dict, None]:
        """Pull events from the run's queue and yield them as SSE dicts."""
        while True:
            try:
                event = await asyncio.wait_for(state.queue.get(), timeout=60.0)
            except asyncio.TimeoutError:
                # Send a keepalive comment to prevent proxy timeouts
                yield {"event": "keepalive", "data": ""}
                continue

            if event.get("__done__"):
                if state.report is not None:
                    yield {
                        "event": "analysis_done",
                        "data": state.report.model_dump_json(),
                    }
                break

            yield {"event": "progress", "data": json.dumps(event)}

    return EventSourceResponse(event_generator())


@app.get("/api/report/{run_id}", tags=["Analysis"])
async def get_report(run_id: str) -> FullReport:
    """Return the completed analysis report as JSON.

    Only available once the pipeline has finished (status == 'done').
    Poll GET /api/progress/{run_id} via SSE to know when it's ready.
    """
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    state = _runs[run_id]

    if state.status == "error":
        raise HTTPException(status_code=500, detail="Analysis pipeline failed for this run.")

    if state.status != "done" or state.report is None:
        raise HTTPException(
            status_code=202,
            detail="Analysis is still in progress. Check /api/progress/{run_id} for updates.",
        )

    return state.report


@app.get("/api/report/{run_id}/pdf", tags=["Analysis"])
async def download_pdf(run_id: str) -> Response:
    """Generate and return the analysis report as a PDF file download.

    Requires the analysis to be complete. The PDF is generated on-demand
    from the stored FullReport using WeasyPrint.
    """
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    state = _runs[run_id]

    if state.status != "done" or state.report is None:
        raise HTTPException(status_code=202, detail="Report not ready yet.")

    try:
        from report.pdf_generator import generate_pdf
        pdf_bytes = await asyncio.to_thread(generate_pdf, state.report)
    except Exception as exc:
        logger.exception("PDF generation failed for run %s", run_id)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc

    filename = f"analysis_{run_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
