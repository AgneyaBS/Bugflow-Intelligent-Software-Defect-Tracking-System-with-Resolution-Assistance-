from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.issue import Issue, IssueStatus, Severity


router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)


# ============================================================
# QUALITY METRICS
# ============================================================

@router.get("/quality-metrics")
def get_quality_metrics(db: Session = Depends(get_db)):

    # --------------------------------------------------------
    # Get all issues
    # --------------------------------------------------------

    issues = db.query(Issue).all()

    total_bugs = len(issues)

    # --------------------------------------------------------
    # Fix Rate
    # Resolved + Closed / Total Bugs * 100
    # --------------------------------------------------------

    resolved_bugs = sum(
        1 for issue in issues
        if issue.status in [
            IssueStatus.RESOLVED,
            IssueStatus.CLOSED
        ]
    )

    if total_bugs > 0:
        fix_rate_percentage = (
            resolved_bugs / total_bugs
        ) * 100
    else:
        fix_rate_percentage = 0.0

    # --------------------------------------------------------
    # Mean Time To Resolution (MTTR)
    # --------------------------------------------------------

    resolution_times = []

    for issue in issues:

        if issue.created_at and issue.resolved_at:

            time_difference = (
                issue.resolved_at - issue.created_at
            )

            hours = time_difference.total_seconds() / 3600

            resolution_times.append(hours)

    if resolution_times:
        mean_time_to_resolution_hours = (
            sum(resolution_times) / len(resolution_times)
        )
    else:
        mean_time_to_resolution_hours = 0.0

    # --------------------------------------------------------
    # Defect Leakage Rate
    #
    # Production bugs / Total Bugs * 100
    #
    # We identify production issues using the
    # environment_details field.
    # --------------------------------------------------------

    production_bugs = 0

    for issue in issues:

        environment = (
            issue.environment_details or ""
        ).lower()

        if "production" in environment:
            production_bugs += 1

    if total_bugs > 0:
        defect_leakage_rate_percentage = (
            production_bugs / total_bugs
        ) * 100
    else:
        defect_leakage_rate_percentage = 0.0

    # --------------------------------------------------------
    # Backlog Health Score
    #
    # Start at 100.
    # Open Critical bugs reduce the score.
    # --------------------------------------------------------

    open_critical_bugs = sum(
        1 for issue in issues
        if issue.severity == Severity.CRITICAL
        and issue.status not in [
            IssueStatus.RESOLVED,
            IssueStatus.CLOSED
        ]
    )

    # Deduct 10 points for every open critical bug.
    backlog_health_score = max(
        0,
        100 - (open_critical_bugs * 10)
    )

    # --------------------------------------------------------
    # Return metrics
    # --------------------------------------------------------

    return {
        "total_bugs": total_bugs,
        "resolved_bugs": resolved_bugs,
        "fix_rate_percentage": round(
            fix_rate_percentage, 2
        ),
        "mean_time_to_resolution_hours": round(
            mean_time_to_resolution_hours, 2
        ),
        "production_bugs": production_bugs,
        "defect_leakage_rate_percentage": round(
            defect_leakage_rate_percentage, 2
        ),
        "open_critical_bugs": open_critical_bugs,
        "backlog_health_score": backlog_health_score
    }
    # ============================================================
# DEFECT TRENDS - LAST 14 DAYS
# ============================================================

@router.get("/defect-trends")
def get_defect_trends(db: Session = Depends(get_db)):

    from datetime import timedelta

    today = datetime.utcnow().date()

    trends = []

    for i in range(13, -1, -1):

        current_date = today - timedelta(days=i)

        next_date = current_date + timedelta(days=1)

        new_bugs = db.query(Issue).filter(
            Issue.created_at >= datetime.combine(
                current_date,
                datetime.min.time()
            ),
            Issue.created_at < datetime.combine(
                next_date,
                datetime.min.time()
            )
        ).count()

        resolved_bugs = db.query(Issue).filter(
            Issue.resolved_at >= datetime.combine(
                current_date,
                datetime.min.time()
            ),
            Issue.resolved_at < datetime.combine(
                next_date,
                datetime.min.time()
            )
        ).count()

        trends.append({
            "date": current_date.isoformat(),
            "new_bugs": new_bugs,
            "resolved_bugs": resolved_bugs
        })

    return {
        "period_days": 14,
        "trends": trends
    }
    # ============================================================
# PLOTLY CHART DATA
# ============================================================

@router.get("/plotly-charts")
def get_plotly_charts(db: Session = Depends(get_db)):

    issues = db.query(Issue).all()

    # --------------------------------------------------------
    # Severity distribution
    # --------------------------------------------------------

    severity_counts = {
        "CRITICAL": 0,
        "MAJOR": 0,
        "MINOR": 0,
        "TRIVIAL": 0
    }

    for issue in issues:
        severity_counts[issue.severity.value] += 1

    # --------------------------------------------------------
    # Workflow pipeline
    # --------------------------------------------------------

    workflow_statuses = [
        "REPORTED",
        "IN_PROGRESS",
        "QA_VERIFICATION",
        "RESOLVED"
    ]

    workflow_counts = {}

    for workflow_status in workflow_statuses:

        workflow_counts[workflow_status] = sum(
            1
            for issue in issues
            if issue.status.value == workflow_status
        )

    # --------------------------------------------------------
    # Defect trends - reuse the same calculation
    # --------------------------------------------------------

    from datetime import timedelta

    today = datetime.utcnow().date()

    trends = []

    for i in range(13, -1, -1):

        current_date = today - timedelta(days=i)
        next_date = current_date + timedelta(days=1)

        new_bugs = db.query(Issue).filter(
            Issue.created_at >= datetime.combine(
                current_date,
                datetime.min.time()
            ),
            Issue.created_at < datetime.combine(
                next_date,
                datetime.min.time()
            )
        ).count()

        resolved_bugs = db.query(Issue).filter(
            Issue.resolved_at >= datetime.combine(
                current_date,
                datetime.min.time()
            ),
            Issue.resolved_at < datetime.combine(
                next_date,
                datetime.min.time()
            )
        ).count()

        trends.append({
            "date": current_date.isoformat(),
            "new_bugs": new_bugs,
            "resolved_bugs": resolved_bugs
        })

    return {
        "defect_trends": trends,
        "severity_distribution": severity_counts,
        "workflow_pipeline": workflow_counts
    }