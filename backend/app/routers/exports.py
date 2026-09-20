import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from fpdf import FPDF
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.models.issue import Issue
from app.models.user import User


router = APIRouter(
    prefix="/api/v1/export",
    tags=["Exports"]
)


def enum_value(value):
    if value is None:
        return ""
    return str(getattr(value, "value", value))


def issue_row(issue: Issue):
    return [
        issue.id,
        issue.project_id,
        issue.reporter_id,
        issue.assignee_id,
        issue.category_id,
        issue.title,
        issue.description,
        enum_value(issue.issue_type),
        enum_value(issue.severity),
        enum_value(issue.priority),
        enum_value(issue.status),
        getattr(issue, "environment_details", ""),
        issue.created_at,
        issue.updated_at,
        issue.resolved_at
    ]


def export_issues_csv(issues, filename):
    output = io.StringIO()
    writer = csv.writer(output)

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

    for issue in issues:
        writer.writerow(issue_row(issue))

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        }
    )


# ============================================================
# ADMIN / SYSTEM-WIDE CSV
# ============================================================

@router.get("/csv")
def export_csv(
    db: Session = Depends(get_db)
):
    issues = (
        db.query(Issue)
        .order_by(Issue.id.asc())
        .all()
    )

    return export_issues_csv(
        issues,
        "bugflow_issues.csv"
    )


# ============================================================
# ADMIN / SYSTEM-WIDE PDF
# ============================================================

def build_pdf_report(
    issues,
    title,
    report_user=None
):
    total = len(issues)
    resolved = sum(
        1
        for issue in issues
        if enum_value(issue.status).upper()
        in {"RESOLVED", "CLOSED"}
    )
    critical = sum(
        1
        for issue in issues
        if enum_value(issue.severity).upper() == "CRITICAL"
    )

    pdf = FPDF()
    pdf.set_auto_page_break(
        auto=True,
        margin=15
    )
    pdf.add_page()

    pdf.set_font("Arial", "B", 18)
    pdf.cell(
        0,
        10,
        title,
        ln=True,
        align="C"
    )

    pdf.ln(5)

    if report_user:
        pdf.set_font("Arial", "", 10)
        pdf.cell(
            0,
            7,
            f"User: {report_user}",
            ln=True
        )
        pdf.ln(3)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(
        0,
        10,
        "Executive Summary",
        ln=True
    )

    pdf.set_font("Arial", "", 10)
    pdf.cell(
        0,
        7,
        f"Total Issues: {total}",
        ln=True
    )
    pdf.cell(
        0,
        7,
        f"Resolved / Closed: {resolved}",
        ln=True
    )
    pdf.cell(
        0,
        7,
        f"Critical Issues: {critical}",
        ln=True
    )

    fix_rate = round(
        (resolved / total) * 100,
        2
    ) if total else 0

    pdf.cell(
        0,
        7,
        f"Fix Rate: {fix_rate}%",
        ln=True
    )

    pdf.ln(5)

    pdf.set_font("Arial", "B", 13)
    pdf.cell(
        0,
        9,
        "Defect Registry",
        ln=True
    )

    pdf.set_font("Arial", "B", 7)
    pdf.cell(14, 7, "ID", 1)
    pdf.cell(52, 7, "Title", 1)
    pdf.cell(23, 7, "Severity", 1)
    pdf.cell(23, 7, "Priority", 1)
    pdf.cell(35, 7, "Status", 1)
    pdf.cell(30, 7, "Created", 1)
    pdf.ln()

    pdf.set_font("Arial", "", 7)

    for issue in issues:
        title_text = str(
            issue.title or "Untitled"
        ).encode(
            "latin-1",
            "replace"
        ).decode("latin-1")

        created = (
            issue.created_at.strftime("%Y-%m-%d")
            if issue.created_at else ""
        )

        pdf.cell(14, 7, str(issue.id), 1)
        pdf.cell(52, 7, title_text[:34], 1)
        pdf.cell(23, 7, enum_value(issue.severity)[:14], 1)
        pdf.cell(23, 7, enum_value(issue.priority)[:14], 1)
        pdf.cell(35, 7, enum_value(issue.status)[:20], 1)
        pdf.cell(30, 7, created, 1)
        pdf.ln()

    data = pdf.output(dest="S")

    if isinstance(data, str):
        data = data.encode("latin-1")
    elif isinstance(data, bytearray):
        data = bytes(data)

    return data


@router.get("/pdf")
def export_pdf(
    db: Session = Depends(get_db)
):
    issues = (
        db.query(Issue)
        .order_by(Issue.id.asc())
        .all()
    )

    pdf_data = build_pdf_report(
        issues,
        "BugFlow - Software Quality Report"
    )

    return StreamingResponse(
        io.BytesIO(pdf_data),
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                'attachment; filename="bugflow_quality_report.pdf"'
        }
    )


# ============================================================
# USER-SPECIFIC EXPORTS
# ============================================================

def get_my_issues(
    db: Session,
    current_user: User
):
    return (
        db.query(Issue)
        .filter(
            (Issue.reporter_id == current_user.id)
            | (Issue.assignee_id == current_user.id)
        )
        .order_by(Issue.id.asc())
        .all()
    )


def safe_user_name(user: User):
    raw_name = (
        user.full_name
        or user.username
        or "User"
    )

    safe = "".join(
        character
        for character in str(raw_name)
        if character.isalnum()
        or character in {" ", "-", "_"}
    ).strip()

    safe = "_".join(safe.split())
    return safe or "User"


@router.get("/my/csv")
def export_my_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    issues = get_my_issues(
        db,
        current_user
    )

    filename = (
        f"bugflow_{safe_user_name(current_user).lower()}"
        "_quality_report.csv"
    )

    return export_issues_csv(
        issues,
        filename
    )


@router.get("/my/pdf")
def export_my_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    issues = get_my_issues(
        db,
        current_user
    )

    display_name = (
        current_user.full_name
        or current_user.username
        or "User"
    )

    pdf_data = build_pdf_report(
        issues,
        "BugFlow - Personal Quality Report",
        report_user=display_name
    )

    filename = (
        f"bugflow_{safe_user_name(current_user).lower()}"
        "_quality_report.pdf"
    )

    return StreamingResponse(
        io.BytesIO(pdf_data),
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        }
    )
