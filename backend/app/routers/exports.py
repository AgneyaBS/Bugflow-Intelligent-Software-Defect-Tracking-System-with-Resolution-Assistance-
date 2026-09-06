import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from fpdf import FPDF
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.issue import Issue


router = APIRouter(
    prefix="/api/v1/export",
    tags=["Exports"]
)


# ============================================================
# CSV EXPORT
# ============================================================

@router.get("/csv")
def export_csv(db: Session = Depends(get_db)):

    issues = (
        db.query(Issue)
        .order_by(Issue.id.asc())
        .all()
    )

    output = io.StringIO()

    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "Issue ID",
        "Project ID",
        "Reporter ID",
        "Assignee ID",
        "Category ID",
        "Title",
        "Description",
        "Issue Type",
        "Severity",
        "Priority",
        "Status",
        "Environment",
        "Created At",
        "Updated At",
        "Resolved At"
    ])

    # Data rows
    for issue in issues:

        writer.writerow([
            issue.id,
            issue.project_id,
            issue.reporter_id,
            issue.assignee_id,
            issue.category_id,
            issue.title,
            issue.description,
            issue.issue_type.value if issue.issue_type else "",
            issue.severity.value if issue.severity else "",
            issue.priority.value if issue.priority else "",
            issue.status.value if issue.status else "",
            issue.environment_details or "",
            issue.created_at,
            issue.updated_at,
            issue.resolved_at
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=bugflow_issue_registry.csv"
        }
    )

# ============================================================
# PDF EXPORT
# ============================================================

@router.get("/pdf")
def export_pdf(db: Session = Depends(get_db)):

    issues = (
        db.query(Issue)
        .order_by(Issue.id.asc())
        .all()
    )

    total_bugs = len(issues)

    resolved_bugs = sum(
        1
        for issue in issues
        if issue.status
        and issue.status.value in ["RESOLVED", "CLOSED"]
    )

    critical_bugs = sum(
        1
        for issue in issues
        if issue.severity
        and issue.severity.value == "CRITICAL"
        and issue.status
        and issue.status.value not in ["RESOLVED", "CLOSED"]
    )

    # --------------------------------------------------------
    # CREATE PDF
    # --------------------------------------------------------

    pdf = FPDF()

    pdf.set_margins(
        left=10,
        top=10,
        right=10
    )

    pdf.set_auto_page_break(
        auto=True,
        margin=15
    )

    pdf.add_page()

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    pdf.set_font("Arial", "B", 20)

    pdf.cell(
        190,
        12,
        "BugFlow - Software Quality Report",
        border=0,
        ln=1,
        align="C"
    )

    pdf.ln(5)

    # --------------------------------------------------------
    # EXECUTIVE SUMMARY
    # --------------------------------------------------------

    pdf.set_font("Arial", "B", 14)

    pdf.cell(
        190,
        10,
        "Executive Summary",
        border=0,
        ln=1
    )

    pdf.set_font("Arial", "", 11)

    pdf.cell(
        190,
        8,
        f"Total Bugs: {total_bugs}",
        border=0,
        ln=1
    )

    pdf.cell(
        190,
        8,
        f"Resolved / Closed Bugs: {resolved_bugs}",
        border=0,
        ln=1
    )

    pdf.cell(
        190,
        8,
        f"Open Critical Bugs: {critical_bugs}",
        border=0,
        ln=1
    )

    pdf.ln(5)

    # --------------------------------------------------------
    # DEFECT REGISTRY
    # --------------------------------------------------------

    pdf.set_font("Arial", "B", 14)

    pdf.cell(
        190,
        10,
        "Defect Registry",
        border=0,
        ln=1
    )

    for issue in issues:

        title = str(issue.title or "Untitled Issue")
        severity = (
            issue.severity.value
            if issue.severity
            else "N/A"
        )
        priority = (
            issue.priority.value
            if issue.priority
            else "N/A"
        )
        status = (
            issue.status.value
            if issue.status
            else "N/A"
        )

        # Remove line breaks and unusual spacing
        title = title.replace("\n", " ")
        title = title.replace("\r", " ")
        title = " ".join(title.split())

        # ----------------------------------------------------
        # VERY IMPORTANT:
        # Limit title length so FPDF never receives a huge
        # unbreakable string.
        # ----------------------------------------------------

        if len(title) > 100:
            title = title[:97] + "..."

        issue_text = (
            f"#{issue.id} - {title}"
        )

        details_text = (
            f"Severity: {severity} | "
            f"Priority: {priority} | "
            f"Status: {status}"
        )

        # ----------------------------------------------------
        # ISSUE TITLE
        # ----------------------------------------------------

        pdf.set_font("Arial", "B", 10)

        pdf.set_x(10)

        pdf.cell(
            190,
            7,
            issue_text,
            border=0,
            ln=1
        )

        # ----------------------------------------------------
        # ISSUE DETAILS
        # ----------------------------------------------------

        pdf.set_font("Arial", "", 9)

        pdf.set_x(10)

        pdf.cell(
            190,
            6,
            details_text,
            border=0,
            ln=1
        )

        pdf.ln(3)

    # --------------------------------------------------------
    # GENERATE PDF
    # --------------------------------------------------------

    pdf_bytes = bytes(pdf.output())

    pdf_stream = io.BytesIO(pdf_bytes)

    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                "attachment; filename=bugflow_quality_report.pdf"
        }
    )