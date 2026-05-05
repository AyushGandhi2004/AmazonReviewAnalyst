"""Standalone PDF generation diagnostic test.

Run from the backend/ directory:
    python -X utf8 test_pdf.py

Checks Jinja2 rendering and WeasyPrint PDF output independently so you
can pinpoint exactly which step fails.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, ".")
os.environ.setdefault("SCRAPINGBEE_API_KEY", "test")
os.environ.setdefault("APIFY_API_TOKEN", "test")
os.environ.setdefault("GROQ_API_KEY", "test")

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
    ReviewSample,
    ReviewSamples,
)


def make_mock_report() -> FullReport:
    """Build a minimal FullReport with realistic data."""
    return FullReport(
        run_id="test-pdf-run-1234",
        your_asin="B0MYPRODUCT",
        competitor_asins=["B0COMPETITOR"],
        created_at=datetime.utcnow(),
        section_1=ReportSection1(products=[
            ProductMetadata(
                asin="B0MYPRODUCT",
                title="SoundMax Pro X Wireless Headphones",
                price="$49.99",
                star_rating=3.8,
                total_reviews=2847,
                bsr="#342 in Headphones",
                bullet_points=["40-hour battery", "Active noise cancellation"],
            ),
            ProductMetadata(
                asin="B0COMPETITOR",
                title="AudioPeak Elite 500",
                price="$79.99",
                star_rating=4.4,
                total_reviews=5621,
                bsr="#87 in Headphones",
                bullet_points=["Premium build quality", "Multipoint Bluetooth"],
            ),
        ]),
        section_2=ReportSection2(summaries=[
            ProductSummary(
                asin="B0MYPRODUCT",
                product_title="SoundMax Pro X Wireless Headphones",
                strengths=["Excellent sound quality", "Long battery life"],
                weaknesses=["Poor build quality", "Bluetooth instability"],
                top_complaints=["Bluetooth drops", "Headband cracks"],
                top_praises=["Amazing bass", "40-hour battery"],
                overall_reaction="Great audio but reliability issues.",
            ),
            ProductSummary(
                asin="B0COMPETITOR",
                product_title="AudioPeak Elite 500",
                strengths=["Premium build", "Reliable Bluetooth"],
                weaknesses=["Shorter battery", "Higher price"],
                top_complaints=["Battery only 20 hours"],
                top_praises=["Rock-solid build", "Perfect Bluetooth"],
                overall_reaction="Premium product with reliable performance.",
            ),
        ]),
        section_3=ReportSection3(comparison=ComparisonResult(
            your_product_advantages=["Lower price", "Longer battery", "ANC"],
            competitor_advantages=[CompetitorAdvantage(
                asin="B0COMPETITOR",
                product_title="AudioPeak Elite 500",
                advantages=["Better build quality", "Better Bluetooth stability"],
            )],
            market_gaps=["No product offers long battery AND premium build"],
            overall_ranking=[
                "1. AudioPeak Elite 500 - best overall",
                "2. SoundMax Pro X - best value",
            ],
        )),
        section_4=ReportSection4(recommendations=RecommendationsResult(recommendations=[
            Recommendation(priority="high", area="product",
                           action="Redesign headband with metal reinforcement.",
                           rationale="Reviews report cracking after 2 months."),
            Recommendation(priority="medium", area="listing",
                           action="Highlight 40-hour battery in title.",
                           rationale="Battery is a top praise but not prominent."),
            Recommendation(priority="low", area="pricing",
                           action="Consider $54.99 with upgraded materials.",
                           rationale="Small increase funds quality improvement."),
        ])),
        section_5=ReportSection5(samples=[
            ReviewSamples(
                asin="B0MYPRODUCT",
                product_title="SoundMax Pro X Wireless Headphones",
                five_star=[
                    ReviewSample(rating=5, title="Amazing sound", text="Bass is incredible.", verified_purchase=True, date="2024-01-10"),
                ],
                one_star=[
                    ReviewSample(rating=1, title="Broke in 2 months", text="Headband cracked.", verified_purchase=True, date="2024-02-01"),
                ],
            ),
        ]),
    )


def sep(label=""):
    print("-" * 60 if not label else f"--- {label} " + "-" * max(1, 56 - len(label)))


def main():
    sep("STEP 1: Import check")
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
        print("[OK] jinja2 imported")
    except ImportError as e:
        print(f"[FAIL] jinja2 import failed: {e}")
        print("  -> Run: pip install jinja2")
        sys.exit(1)

    try:
        from xhtml2pdf import pisa
        print("[OK] xhtml2pdf imported")
    except ImportError as e:
        print(f"[FAIL] xhtml2pdf import failed: {e}")
        print("  -> Run: pip install xhtml2pdf reportlab")
        sys.exit(1)
    except Exception as e:
        print(f"[FAIL] xhtml2pdf failed to load: {e}")
        sys.exit(1)

    sep("STEP 2: Template path")
    templates_dir = Path(__file__).parent / "templates"
    template_file = templates_dir / "report.html"
    print(f"Templates dir : {templates_dir}")
    print(f"Template file : {template_file}")
    if not template_file.exists():
        print("[FAIL] report.html not found!")
        sys.exit(1)
    print("[OK] report.html found")

    sep("STEP 3: Jinja2 rendering")
    report = make_mock_report()
    try:
        env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template("report.html")
        html_str = template.render(report=report)
        print(f"[OK] HTML rendered ({len(html_str)} chars)")
    except Exception as e:
        print(f"[FAIL] Jinja2 rendering failed: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    sep("STEP 4: xhtml2pdf PDF generation")
    try:
        from io import BytesIO
        from xhtml2pdf import pisa
        buffer = BytesIO()
        result = pisa.CreatePDF(src=html_str.encode("utf-8"), dest=buffer, encoding="utf-8")
        if result.err:
            print(f"[FAIL] xhtml2pdf reported {result.err} error(s)")
            sys.exit(1)
        pdf_bytes = buffer.getvalue()
        print(f"[OK] PDF generated ({len(pdf_bytes)} bytes)")
    except Exception as e:
        print(f"[FAIL] xhtml2pdf failed: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    sep("STEP 5: Save to disk")
    out_path = Path("test_report_output.pdf")
    out_path.write_bytes(pdf_bytes)
    print(f"[OK] Saved to {out_path.resolve()}")

    sep()
    print("All steps PASSED. PDF generation is working.")


if __name__ == "__main__":
    main()
