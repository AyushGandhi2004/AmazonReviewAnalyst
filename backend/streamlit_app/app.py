"""Streamlit UI for the Amazon Review Analyzer (Phase 6).

Connects to the FastAPI backend only — never calls scrapers or LLM directly.
Run with:
    streamlit run streamlit_app/app.py
"""

import json
import os

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Amazon Review Analyzer",
    page_icon="magnifying glass",
    layout="wide",
)

# ─────────────────────────────────────────────
# Session state helpers
# ─────────────────────────────────────────────

def _init_state() -> None:
    defaults = {
        "phase": "input",      # input | analyzing | done | error
        "run_id": None,
        "report": None,
        "error_msg": None,
        "steps": [],           # list of (step_label, pct, status)
        "progress_pct": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ─────────────────────────────────────────────
# Backend helpers
# ─────────────────────────────────────────────

def _post_analyze(your_asin: str, competitor_asins: list[str]) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/analyze",
        json={"your_asin": your_asin, "competitor_asins": competitor_asins},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def _stream_progress(run_id: str, progress_bar, steps_placeholder):
    """Consume the SSE progress stream and update UI elements in real-time.

    Parses raw SSE lines (event: / data:) from the streaming response.
    Returns the final FullReport dict when the analysis_done event arrives,
    or raises RuntimeError on pipeline error.
    """
    url = f"{API_BASE}/api/progress/{run_id}"
    steps = st.session_state["steps"]

    with requests.get(url, stream=True, timeout=900) as resp:
        resp.raise_for_status()

        current_event = None
        for raw_line in resp.iter_lines(decode_unicode=True):
            if raw_line.startswith("event:"):
                current_event = raw_line[len("event:"):].strip()
            elif raw_line.startswith("data:"):
                data_str = raw_line[len("data:"):].strip()
                if not data_str:
                    continue

                if current_event == "analysis_done":
                    return json.loads(data_str)

                if current_event == "progress":
                    try:
                        evt = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    if evt.get("status") == "error":
                        raise RuntimeError(evt.get("message", "Pipeline error"))

                    pct = evt.get("progress_pct", 0)
                    step = evt.get("step", "")
                    status = evt.get("status", "")

                    st.session_state["progress_pct"] = pct
                    progress_bar.progress(pct / 100)

                    icon = "✓" if status == "done" else "..." if status == "running" else ""
                    steps.append(f"{icon} {step}")
                    steps_placeholder.markdown("\n".join(f"- {s}" for s in steps))

                current_event = None  # reset after consuming data line

    return None


# ─────────────────────────────────────────────
# UI: Input phase
# ─────────────────────────────────────────────

def _render_input() -> None:
    st.title("Amazon Competitor Review Analytics")
    st.markdown(
        "Paste your product ASIN and up to 3 competitor ASINs to receive a full "
        "AI-powered competitive analysis report backed by real customer review data."
    )

    with st.form("asin_form"):
        st.subheader("Enter ASINs")
        your_asin = st.text_input("Your Product ASIN *", placeholder="e.g. B08N5WRWNW")
        comp1 = st.text_input("Competitor ASIN 1 (optional)", placeholder="e.g. B07XJ8C8F5")
        comp2 = st.text_input("Competitor ASIN 2 (optional)")
        comp3 = st.text_input("Competitor ASIN 3 (optional)")
        submitted = st.form_submit_button("Run Analysis", type="primary", use_container_width=True)

    if submitted:
        your_asin = your_asin.strip().upper()
        competitors = [a.strip().upper() for a in [comp1, comp2, comp3] if a.strip()]

        if not your_asin:
            st.error("Please enter your product ASIN.")
            return

        try:
            result = _post_analyze(your_asin, competitors)
        except requests.HTTPError as e:
            try:
                detail = e.response.json().get("detail", str(e))
            except Exception:
                detail = str(e)
            st.error(f"Validation error: {detail}")
            return
        except requests.ConnectionError:
            st.error(f"Cannot connect to backend at {API_BASE}. Is the FastAPI server running?")
            return

        st.session_state["run_id"] = result["run_id"]
        st.session_state["phase"] = "analyzing"
        st.session_state["steps"] = []
        st.session_state["progress_pct"] = 0
        st.rerun()


# ─────────────────────────────────────────────
# UI: Analyzing phase
# ─────────────────────────────────────────────

def _render_analyzing() -> None:
    st.title("Analyzing...")
    st.markdown(f"**Run ID:** `{st.session_state['run_id']}`")

    progress_bar = st.progress(0)
    steps_placeholder = st.empty()
    status_text = st.empty()

    status_text.info("Connecting to analysis pipeline...")

    try:
        report_data = _stream_progress(
            st.session_state["run_id"],
            progress_bar,
            steps_placeholder,
        )
    except RuntimeError as e:
        st.session_state["phase"] = "error"
        st.session_state["error_msg"] = str(e)
        st.rerun()
        return
    except Exception as e:
        st.session_state["phase"] = "error"
        st.session_state["error_msg"] = f"Unexpected error: {e}"
        st.rerun()
        return

    progress_bar.progress(1.0)
    status_text.success("Analysis complete!")

    st.session_state["report"] = report_data
    st.session_state["phase"] = "done"
    st.rerun()


# ─────────────────────────────────────────────
# UI: Error phase
# ─────────────────────────────────────────────

def _render_error() -> None:
    st.title("Analysis Failed")
    st.error(st.session_state.get("error_msg", "An unknown error occurred."))
    if st.button("Start Over"):
        for k in ["phase", "run_id", "report", "error_msg", "steps", "progress_pct"]:
            st.session_state.pop(k, None)
        st.rerun()


# ─────────────────────────────────────────────
# UI: Report phase helpers
# ─────────────────────────────────────────────

_PRIORITY_COLORS = {
    "high": "#d9534f",
    "medium": "#f0ad4e",
    "low": "#5cb85c",
}

_AREA_LABELS = {
    "product": "Product",
    "listing": "Listing",
    "pricing": "Pricing",
}


def _badge(label: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:white;padding:2px 8px;'
        f'border-radius:4px;font-size:0.75rem;font-weight:bold">{label}</span>'
    )


def _render_section1(report: dict) -> None:
    """Side-by-side metrics table."""
    st.subheader("Product Metrics")
    products = report.get("section_1", {}).get("products", [])
    if not products:
        st.info("No product metadata available.")
        return

    cols = st.columns(len(products))
    for col, p in zip(cols, products):
        with col:
            st.markdown(f"**{p.get('title') or p.get('asin')}**")
            st.markdown(f"ASIN: `{p.get('asin')}`")
            price = p.get("price") or "N/A"
            rating = p.get("star_rating") or "N/A"
            total = p.get("total_reviews") or "N/A"
            bsr = p.get("bsr") or "N/A"
            st.metric("Price", price)
            st.metric("Star Rating", f"{rating} / 5")
            st.metric("Total Reviews", f"{total:,}" if isinstance(total, int) else total)
            st.markdown(f"**BSR:** {bsr}")

    # Also show as a comparison table
    st.divider()
    rows = []
    for p in products:
        rows.append({
            "Product": p.get("title") or p.get("asin"),
            "ASIN": p.get("asin"),
            "Price": p.get("price") or "N/A",
            "Rating": p.get("star_rating") or "N/A",
            "Reviews": p.get("total_reviews") or "N/A",
            "BSR": p.get("bsr") or "N/A",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_section2(report: dict) -> None:
    """Expandable AI summary cards per product."""
    st.subheader("AI Review Summaries")
    summaries = report.get("section_2", {}).get("summaries", [])
    if not summaries:
        st.info("No summaries available.")
        return

    for s in summaries:
        title = s.get("product_title") or s.get("asin")
        with st.expander(f"{title}", expanded=True):
            overall = s.get("overall_reaction") or ""
            if overall:
                st.info(overall)

            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown("**Strengths**")
                for item in s.get("strengths") or []:
                    st.markdown(f"- {item}")
                st.markdown("**Top Praises**")
                for item in s.get("top_praises") or []:
                    if isinstance(item, dict):
                        text = item.get("praise") or item.get("text") or str(item)
                        freq = item.get("frequency")
                        st.markdown(f"- {text} *(×{freq})*" if freq else f"- {text}")
                    else:
                        st.markdown(f"- {item}")
            with col_r:
                st.markdown("**Weaknesses**")
                for item in s.get("weaknesses") or []:
                    st.markdown(f"- {item}")
                st.markdown("**Top Complaints**")
                for item in s.get("top_complaints") or []:
                    if isinstance(item, dict):
                        text = item.get("complaint") or item.get("text") or str(item)
                        freq = item.get("frequency")
                        st.markdown(f"- {text} *(×{freq})*" if freq else f"- {text}")
                    else:
                        st.markdown(f"- {item}")

    # Overall ranking + market gaps from section 3
    comp = report.get("section_3", {}).get("comparison", {})
    ranking = comp.get("overall_ranking") or []
    gaps = comp.get("market_gaps") or []

    if ranking:
        st.divider()
        st.subheader("Overall Ranking")
        for r in ranking:
            st.markdown(f"- {r}")

    if gaps:
        st.divider()
        st.subheader("Market Gaps")
        for g in gaps:
            st.markdown(f"- {g}")


def _render_section3(report: dict) -> None:
    """Cross-product comparison."""
    st.subheader("Competitive Comparison")
    comp = report.get("section_3", {}).get("comparison", {})
    if not comp:
        st.info("No comparison data available.")
        return

    your_adv = comp.get("your_product_advantages") or []
    if your_adv:
        st.markdown("**Your Product Advantages**")
        for a in your_adv:
            st.markdown(f"- {a}")

    comp_advs = comp.get("competitor_advantages") or []
    if comp_advs:
        st.divider()
        st.markdown("**Competitor Advantages**")
        for ca in comp_advs:
            title = ca.get("product_title") or ca.get("asin")
            with st.expander(title):
                for a in ca.get("advantages") or []:
                    st.markdown(f"- {a}")

    ranking = comp.get("overall_ranking") or []
    if ranking:
        st.divider()
        st.markdown("**Overall Ranking**")
        for r in ranking:
            st.markdown(f"- {r}")

    gaps = comp.get("market_gaps") or []
    if gaps:
        st.divider()
        st.markdown("**Market Gaps**")
        for g in gaps:
            st.markdown(f"- {g}")


def _render_review_card(review: dict, sentiment: str) -> None:
    rating = review.get("rating") or "?"
    title = review.get("title") or ""
    text = review.get("text") or ""
    date = review.get("date") or ""
    verified = review.get("verified_purchase", False)

    stars = "★" * int(rating) if isinstance(rating, int) else str(rating)
    verified_badge = " ✓ Verified" if verified else ""
    header = f"{stars} — {title}" if title else stars
    meta = f"*{date}{verified_badge}*" if date else f"*{verified_badge.strip()}*"

    st.markdown(f"**{header}**  \n{meta}")
    st.markdown(f"> {text}")


def _render_section5(report: dict) -> None:
    """Review samples — top 3 five-star and 1-star per product."""
    st.subheader("Customer Review Samples")
    samples_list = report.get("section_5", {}).get("samples", [])
    if not samples_list:
        st.info("No review samples available.")
        return

    for samples in samples_list:
        title = samples.get("product_title") or samples.get("asin")
        st.markdown(f"### {title}")
        col_five, col_one = st.columns(2)

        with col_five:
            st.markdown("**5-Star Reviews**")
            five_stars = samples.get("five_star") or []
            if five_stars:
                for r in five_stars:
                    _render_review_card(r, "positive")
                    st.markdown("---")
            else:
                st.caption("None collected.")

        with col_one:
            st.markdown("**1-Star Reviews**")
            one_stars = samples.get("one_star") or []
            if one_stars:
                for r in one_stars:
                    _render_review_card(r, "negative")
                    st.markdown("---")
            else:
                st.caption("None collected.")


def _render_section4(report: dict) -> None:
    """Seller recommendations sorted high→medium→low."""
    st.subheader("Seller Recommendations")
    recs = report.get("section_4", {}).get("recommendations", {}).get("recommendations") or []
    if not recs:
        st.info("No recommendations available.")
        return

    for rec in recs:
        priority = rec.get("priority", "medium")
        area = rec.get("area", "product")
        action = rec.get("action", "")
        rationale = rec.get("rationale", "")

        p_color = _PRIORITY_COLORS.get(priority, "#999")
        a_label = _AREA_LABELS.get(area, area.capitalize())

        priority_badge = _badge(priority.upper(), p_color)
        area_badge = _badge(a_label, "#555")

        st.markdown(
            f"{priority_badge}&nbsp;{area_badge}&nbsp; **{action}**",
            unsafe_allow_html=True,
        )
        if rationale:
            st.caption(rationale)
        st.markdown("---")


# ─────────────────────────────────────────────
# UI: Done / report phase
# ─────────────────────────────────────────────

def _render_done() -> None:
    report = st.session_state.get("report") or {}
    run_id = st.session_state.get("run_id", "")

    your_asin = report.get("your_asin", "")
    # Try to resolve product title from section 1
    products = report.get("section_1", {}).get("products", [])
    your_title = next(
        (p.get("title") for p in products if p.get("asin") == your_asin),
        your_asin,
    )

    st.title("Analysis Report")
    st.markdown(f"**Product:** {your_title}  |  **Run ID:** `{run_id}`")

    # PDF download button (placeholder — Phase 7)
    pdf_url = f"{API_BASE}/api/report/{run_id}/pdf"
    col_dl, col_restart = st.columns([1, 5])
    with col_dl:
        st.link_button("Download PDF", pdf_url)
    with col_restart:
        if st.button("New Analysis"):
            for k in ["phase", "run_id", "report", "error_msg", "steps", "progress_pct"]:
                st.session_state.pop(k, None)
            st.rerun()

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "Product Metrics",
        "AI Analysis",
        "Review Samples",
        "Recommendations",
    ])

    with tab1:
        _render_section1(report)

    with tab2:
        _render_section2(report)

    with tab3:
        _render_section5(report)

    with tab4:
        _render_section4(report)


# ─────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────

phase = st.session_state["phase"]

if phase == "input":
    _render_input()
elif phase == "analyzing":
    _render_analyzing()
elif phase == "done":
    _render_done()
elif phase == "error":
    _render_error()
