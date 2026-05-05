"""Server-Sent Events (SSE) helpers for streaming analysis progress."""

import json
from typing import AsyncGenerator

from models import ProgressEvent


def format_sse_event(event: ProgressEvent, event_type: str = "progress") -> str:
    """Serialize a ProgressEvent into the SSE wire format.

    SSE format:
        event: <event_type>\\n
        data: <json>\\n\\n
    """
    return f"event: {event_type}\ndata: {event.model_dump_json()}\n\n"


def make_progress_event(
    step: str,
    status: str,
    progress_pct: int,
    message: str | None = None,
) -> ProgressEvent:
    """Convenience constructor for a ProgressEvent."""
    return ProgressEvent(
        step=step,
        status=status,
        progress_pct=progress_pct,
        message=message,
    )


def make_error_event(step: str, error_message: str) -> str:
    """Format an error SSE event."""
    event = ProgressEvent(
        step=step,
        status="error",
        progress_pct=0,
        message=error_message,
    )
    return format_sse_event(event, event_type="error")


def make_done_event(report_json: str) -> str:
    """Format the final 'analysis_done' SSE event carrying the full report.

    The report JSON is embedded as the data payload under key 'report'.
    """
    payload = json.dumps({"report": json.loads(report_json)})
    return f"event: analysis_done\ndata: {payload}\n\n"
