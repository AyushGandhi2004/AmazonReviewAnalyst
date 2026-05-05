"""PDF generation from the Jinja2 HTML report template using xhtml2pdf.

xhtml2pdf is pure Python and requires no system libraries (no GTK/Cairo),
making it work on Windows without any additional installation steps.
All CSS in the template uses only properties supported by xhtml2pdf.
"""

import logging
from io import BytesIO
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from xhtml2pdf import pisa

from models import FullReport

logger = logging.getLogger(__name__)

# Resolve templates dir relative to this file so it works from any CWD
_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def generate_pdf(report: FullReport) -> bytes:
    """Render a FullReport as a PDF and return raw bytes.

    Loads the Jinja2 template from backend/templates/report.html,
    renders it with the report data, then converts HTML to PDF via
    xhtml2pdf (pure Python, no system dependencies).

    Args:
        report: The fully assembled FullReport to render.

    Returns:
        Raw PDF bytes ready to return as a file download response.

    Raises:
        RuntimeError: If template rendering or PDF conversion fails.
    """
    try:
        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template("report.html")
        html_str = template.render(report=report)
    except Exception as exc:
        raise RuntimeError(f"Template rendering failed: {exc}") from exc

    try:
        buffer = BytesIO()
        result = pisa.CreatePDF(
            src=html_str.encode("utf-8"),
            dest=buffer,
            encoding="utf-8",
        )
        if result.err:
            raise RuntimeError(f"xhtml2pdf reported {result.err} error(s) during conversion.")
        pdf_bytes = buffer.getvalue()
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"PDF conversion failed: {exc}") from exc

    logger.info(
        "PDF generated for run %s (%d bytes)", report.run_id, len(pdf_bytes)
    )
    return pdf_bytes
