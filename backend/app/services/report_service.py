from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def get_enum_value(value):
    """
    Return the actual value of an Enum.
    If the value is not an Enum, return it as a string.
    """

    if value is None:
        return ""

    return getattr(value, "value", str(value))


def generate_issue_report(issues):
    """
    Generate a PDF report containing issue information.
    """

    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    width, height = A4

    # ========================================================
    # REPORT TITLE
    # ========================================================

    pdf.setFont("Helvetica-Bold", 20)

    pdf.drawString(
        50,
        height - 50,
        "BugFlow - Issue Report"
    )

    pdf.setFont("Helvetica", 10)

    pdf.drawString(
        50,
        height - 70,
        "Software Issue Tracking & Resolution Platform"
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    total_issues = len(issues)

    resolved_issues = sum(
        1
        for issue in issues
        if get_enum_value(issue.status)
        in ["RESOLVED", "CLOSED"]
    )

    open_issues = total_issues - resolved_issues

    y = height - 110

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    pdf.drawString(
        50,
        y,
        "Summary"
    )

    y -= 20

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawString(
        50,
        y,
        f"Total Issues: {total_issues}"
    )

    y -= 15

    pdf.drawString(
        50,
        y,
        f"Open Issues: {open_issues}"
    )

    y -= 15

    pdf.drawString(
        50,
        y,
        f"Resolved / Closed: {resolved_issues}"
    )

    # ========================================================
    # ISSUE DETAILS
    # ========================================================

    y -= 35

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    pdf.drawString(
        50,
        y,
        "Issue Details"
    )

    y -= 25

    for issue in issues:

        # Start a new page when space is low
        if y < 100:

            pdf.showPage()

            y = height - 50

        # ----------------------------------------------------
        # ISSUE NUMBER
        # ----------------------------------------------------

        pdf.setFont(
            "Helvetica-Bold",
            10
        )

        pdf.drawString(
            50,
            y,
            f"Issue #{issue.id}"
        )

        y -= 15

        # ----------------------------------------------------
        # ISSUE VALUES
        # ----------------------------------------------------

        pdf.setFont(
            "Helvetica",
            9
        )

        title = str(
            getattr(issue, "title", "")
        )

        status = get_enum_value(
            getattr(issue, "status", None)
        )

        priority = get_enum_value(
            getattr(issue, "priority", None)
        )

        severity = get_enum_value(
            getattr(issue, "severity", None)
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        pdf.drawString(
            65,
            y,
            f"Title: {title[:80]}"
        )

        y -= 14

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        pdf.drawString(
            65,
            y,
            f"Status: {status}"
        )

        y -= 14

        # ----------------------------------------------------
        # PRIORITY
        # ----------------------------------------------------

        pdf.drawString(
            65,
            y,
            f"Priority: {priority}"
        )

        y -= 14

        # ----------------------------------------------------
        # SEVERITY
        # ----------------------------------------------------

        pdf.drawString(
            65,
            y,
            f"Severity: {severity}"
        )

        y -= 25

    # ========================================================
    # FINISH PDF
    # ========================================================

    pdf.save()

    buffer.seek(0)

    return buffer