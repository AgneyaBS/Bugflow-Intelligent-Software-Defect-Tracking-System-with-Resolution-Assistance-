from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.models.issue import Issue, IssueStatus, Severity
from app.models.user import User


router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)


# ============================================================
# HELPERS
# ============================================================

def enum_value(value: Any) -> str:
    """Return an enum's value as an uppercase string."""
    if value is None:
        return ""
    return str(getattr(value, "value", value)).upper()


def resolution_hours(issue: Issue):
    """Return issue resolution time in hours when available."""
    if not issue.created_at or not issue.resolved_at:
        return None

    try:
        hours = (
            issue.resolved_at - issue.created_at
        ).total_seconds() / 3600
        return hours if hours >= 0 else None
    except Exception:
        return None


def is_resolved(issue: Issue) -> bool:
    return enum_value(issue.status) in {
        "RESOLVED",
        "CLOSED"
    }


def is_production_issue(issue: Issue) -> bool:
    environment = getattr(
        issue,
        "environment_details",
        None
    )
    return bool(
        environment
        and "production" in str(environment).lower()
    )


def user_issue_query(
    db: Session,
    current_user: User
):
    """Issues reported by OR assigned to the logged-in user."""
    return (
        db.query(Issue)
        .filter(
            (Issue.reporter_id == current_user.id)
            | (Issue.assignee_id == current_user.id)
        )
    )


# ============================================================
# ADMIN / SYSTEM-WIDE QUALITY METRICS
# KEEPING EXISTING ADMIN ENDPOINT SEMANTICS
# ============================================================

@router.get("/quality-metrics")
def quality_metrics(
    db: Session = Depends(get_db)
):
    issues = db.query(Issue).all()

    total_bugs = len(issues)
    resolved_count = sum(
        1 for issue in issues if is_resolved(issue)
    )

    fix_rate = round(
        (resolved_count / total_bugs) * 100,
        2
    ) if total_bugs else 0

    resolution_times = [
        hours
        for issue in issues
        if (hours := resolution_hours(issue)) is not None
    ]

    mttr = round(
        sum(resolution_times) / len(resolution_times),
        2
    ) if resolution_times else 0

    production_bugs = sum(
        1 for issue in issues
        if is_production_issue(issue)
    )

    defect_leakage = round(
        (production_bugs / total_bugs) * 100,
        2
    ) if total_bugs else 0

    open_critical = sum(
        1
        for issue in issues
        if enum_value(issue.severity) == "CRITICAL"
        and not is_resolved(issue)
    )

    backlog_health = round(
        max(
            0,
            100 - (
                (open_critical / total_bugs) * 100
            )
        ),
        2
    ) if total_bugs else 100

    return {
        "total_bugs": total_bugs,
        "fix_rate_percentage": fix_rate,
        "mean_time_to_resolution_hours": mttr,
        "defect_leakage_rate_percentage": defect_leakage,
        "open_critical_bugs": open_critical,
        "backlog_health_score": backlog_health
    }


# ============================================================
# ADMIN / SYSTEM-WIDE DEFECT TRENDS
# ============================================================

@router.get("/defect-trends")
def defect_trends(
    db: Session = Depends(get_db)
):
    issues = db.query(Issue).all()

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=13)

    trends = []

    for offset in range(14):
        current_date = start_date + timedelta(days=offset)

        new_bugs = sum(
            1
            for issue in issues
            if issue.created_at
            and issue.created_at.date() == current_date
        )

        resolved_bugs = sum(
            1
            for issue in issues
            if issue.resolved_at
            and issue.resolved_at.date() == current_date
        )

        trends.append({
            "date": current_date.isoformat(),
            "new_bugs": new_bugs,
            "resolved_bugs": resolved_bugs
        })

    return {
        "trends": trends
    }


# ============================================================
# ADMIN / SYSTEM-WIDE PLOTLY DATA
# ============================================================

@router.get("/plotly-charts")
def plotly_charts(
    db: Session = Depends(get_db)
):
    issues = db.query(Issue).all()

    severity_distribution = {
        "CRITICAL": 0,
        "MAJOR": 0,
        "MINOR": 0,
        "TRIVIAL": 0
    }

    for issue in issues:
        severity = enum_value(issue.severity)
        if severity in severity_distribution:
            severity_distribution[severity] += 1

    workflow_pipeline = {
        "REPORTED": 0,
        "TRIAGED": 0,
        "IN_PROGRESS": 0,
        "CODE_REVIEW": 0,
        "QA_VERIFICATION": 0,
        "RESOLVED": 0,
        "CLOSED": 0
    }

    for issue in issues:
        status_value = enum_value(issue.status)
        if status_value in workflow_pipeline:
            workflow_pipeline[status_value] += 1

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=13)

    trends = []
    for offset in range(14):
        current_date = start_date + timedelta(days=offset)

        trends.append({
            "date": current_date.isoformat(),
            "new_bugs": sum(
                1
                for issue in issues
                if issue.created_at
                and issue.created_at.date() == current_date
            ),
            "resolved_bugs": sum(
                1
                for issue in issues
                if issue.resolved_at
                and issue.resolved_at.date() == current_date
            )
        })

    return {
        "severity_distribution": severity_distribution,
        "workflow_pipeline": workflow_pipeline,
        "trends": trends
    }


# ============================================================
# ADMIN / SYSTEM-WIDE DEVELOPER WORKLOAD
# ============================================================

@router.get("/developer-workload")
def developer_workload(
    db: Session = Depends(get_db)
):
    developers = (
        db.query(User)
        .filter(User.role == "DEVELOPER")
        .all()
    )

    # If the database uses a different role naming convention,
    # include users who have developer-like skills as a fallback.
    if not developers:
        developers = (
            db.query(User)
            .filter(User.is_active.is_(True))
            .all()
        )

    all_issues = db.query(Issue).all()
    results = []

    for developer in developers:
        active = [
            issue
            for issue in all_issues
            if issue.assignee_id == developer.id
            and enum_value(issue.status) in {
                "IN_PROGRESS",
                "CODE_REVIEW"
            }
        ]

        completed = [
            issue
            for issue in all_issues
            if issue.assignee_id == developer.id
            and enum_value(issue.status) in {
                "RESOLVED",
                "CLOSED"
            }
        ]

        times = [
            hours
            for issue in completed
            if (hours := resolution_hours(issue)) is not None
        ]

        avg_mttr = round(
            sum(times) / len(times),
            2
        ) if times else 0

        active_count = len(active)

        if active_count >= 6:
            workload = "HIGH"
        elif active_count >= 3:
            workload = "MEDIUM"
        else:
            workload = "BALANCED"

        results.append({
            "user_id": developer.id,
            "username": developer.username,
            "full_name": developer.full_name,
            "team": developer.team or "Unassigned",
            "active_tasks": active_count,
            "completed_fixes": len(completed),
            "avg_mttr_hours": avg_mttr,
            "workload_status": workload
        })

    return {
        "total_developers": len(results),
        "developers": results
    }


# ============================================================
# USER-SPECIFIC ANALYTICS
# ============================================================

@router.get("/my/quality-metrics")
def my_quality_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    issues = user_issue_query(
        db,
        current_user
    ).all()

    total_bugs = len(issues)
    resolved_count = sum(
        1 for issue in issues if is_resolved(issue)
    )

    fix_rate = round(
        (resolved_count / total_bugs) * 100,
        2
    ) if total_bugs else 0

    resolution_times = [
        hours
        for issue in issues
        if (hours := resolution_hours(issue)) is not None
    ]

    mttr = round(
        sum(resolution_times) / len(resolution_times),
        2
    ) if resolution_times else 0

    production_bugs = sum(
        1 for issue in issues
        if is_production_issue(issue)
    )

    defect_leakage = round(
        (production_bugs / total_bugs) * 100,
        2
    ) if total_bugs else 0

    open_critical = sum(
        1
        for issue in issues
        if enum_value(issue.severity) == "CRITICAL"
        and not is_resolved(issue)
    )

    backlog_health = round(
        max(
            0,
            100 - (
                (open_critical / total_bugs) * 100
            )
        ),
        2
    ) if total_bugs else 100

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "total_bugs": total_bugs,
        "fix_rate_percentage": fix_rate,
        "mean_time_to_resolution_hours": mttr,
        "defect_leakage_rate_percentage": defect_leakage,
        "open_critical_bugs": open_critical,
        "backlog_health_score": backlog_health
    }


@router.get("/my/defect-trends")
def my_defect_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    issues = user_issue_query(
        db,
        current_user
    ).all()

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=13)

    trends = []

    for offset in range(14):
        current_date = start_date + timedelta(days=offset)

        new_bugs = sum(
            1
            for issue in issues
            if issue.created_at
            and issue.created_at.date() == current_date
        )

        resolved_bugs = sum(
            1
            for issue in issues
            if issue.resolved_at
            and issue.resolved_at.date() == current_date
        )

        trends.append({
            "date": current_date.isoformat(),
            "new_bugs": new_bugs,
            "resolved_bugs": resolved_bugs
        })

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "trends": trends
    }


@router.get("/my/plotly-charts")
def my_plotly_charts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    issues = user_issue_query(
        db,
        current_user
    ).all()

    severity_distribution = {
        "CRITICAL": 0,
        "MAJOR": 0,
        "MINOR": 0,
        "TRIVIAL": 0
    }

    for issue in issues:
        severity = enum_value(issue.severity)
        if severity in severity_distribution:
            severity_distribution[severity] += 1

    workflow_pipeline = {
        "REPORTED": 0,
        "TRIAGED": 0,
        "IN_PROGRESS": 0,
        "CODE_REVIEW": 0,
        "QA_VERIFICATION": 0,
        "RESOLVED": 0,
        "CLOSED": 0
    }

    for issue in issues:
        status_value = enum_value(issue.status)
        if status_value in workflow_pipeline:
            workflow_pipeline[status_value] += 1

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=13)

    trends = []
    for offset in range(14):
        current_date = start_date + timedelta(days=offset)

        trends.append({
            "date": current_date.isoformat(),
            "new_bugs": sum(
                1
                for issue in issues
                if issue.created_at
                and issue.created_at.date() == current_date
            ),
            "resolved_bugs": sum(
                1
                for issue in issues
                if issue.resolved_at
                and issue.resolved_at.date() == current_date
            )
        })

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "severity_distribution": severity_distribution,
        "workflow_pipeline": workflow_pipeline,
        "trends": trends
    }
