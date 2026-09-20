import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.models.audit_log import AuditLog
from app.models.issue import Issue, IssueStatus
from app.models.user import User


router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Webhooks"]
)


class GitWebhookPayload(BaseModel):
    message: str
    commit_hash: str


def enum_value(value):
    if value is None:
        return ""
    return str(getattr(value, "value", value))


def extract_issue_id(message: str):
    match = re.search(
        r"(?:fixes|closes|resolves)\s+#(\d+)",
        message or "",
        re.IGNORECASE
    )

    return int(match.group(1)) if match else None


# ============================================================
# ADMIN / SYSTEM-WIDE WEBHOOK ISSUE LIST
# ============================================================

@router.get("/issues")
def get_webhook_issues(
    db: Session = Depends(get_db)
):
    issues = (
        db.query(Issue)
        .order_by(Issue.id.desc())
        .all()
    )

    return [
        {
            "id": issue.id,
            "title": issue.title,
            "status": enum_value(issue.status)
        }
        for issue in issues
    ]


# ============================================================
# ADMIN / SYSTEM-WIDE GIT WEBHOOK
# Existing endpoint intentionally remains system-wide.
# ============================================================

@router.post("/git")
def git_webhook(
    payload: GitWebhookPayload,
    db: Session = Depends(get_db)
):
    issue_id = extract_issue_id(payload.message)

    if issue_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No issue reference found. Use fixes #123, "
                "closes #123, or resolves #123."
            )
        )

    issue = (
        db.query(Issue)
        .filter(Issue.id == issue_id)
        .first()
    )

    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )

    old_status = enum_value(issue.status)

    if issue.status in (
        IssueStatus.QA_VERIFICATION,
        IssueStatus.RESOLVED,
        IssueStatus.CLOSED
    ):
        return {
            "success": True,
            "message": (
                "Issue is already in QA verification "
                "or completed."
            ),
            "issue_id": issue.id,
            "status": old_status,
            "commit_hash": payload.commit_hash
        }

    issue.status = IssueStatus.QA_VERIFICATION

    admin = (
        db.query(User)
        .filter(
            User.role == "ADMIN",
            User.is_active.is_(True)
        )
        .order_by(User.id.asc())
        .first()
    )

    if admin:
        audit = AuditLog(
            issue_id=issue.id,
            user_id=admin.id,
            action="GIT_WEBHOOK",
            field_name="status",
            old_value=old_status,
            new_value="QA_VERIFICATION"
        )
        db.add(audit)

    db.commit()
    db.refresh(issue)

    return {
        "success": True,
        "message": (
            f"Issue #{issue.id} moved to QA verification."
        ),
        "issue_id": issue.id,
        "status": enum_value(issue.status),
        "commit_hash": payload.commit_hash
    }


# ============================================================
# USER-SPECIFIC WEBHOOK ISSUE LIST
# ============================================================

@router.get("/my/issues")
def get_my_webhook_issues(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    issues = (
        db.query(Issue)
        .filter(
            (Issue.reporter_id == current_user.id)
            | (Issue.assignee_id == current_user.id)
        )
        .order_by(Issue.id.desc())
        .all()
    )

    return [
        {
            "id": issue.id,
            "title": issue.title,
            "status": enum_value(issue.status)
        }
        for issue in issues
    ]


# ============================================================
# USER-SPECIFIC GIT WEBHOOK
# ============================================================

@router.post("/my/git")
def my_git_webhook(
    payload: GitWebhookPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    issue_id = extract_issue_id(payload.message)

    if issue_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No issue reference found. Use fixes #123, "
                "closes #123, or resolves #123."
            )
        )

    # Security boundary: issue ownership is checked in the query.
    issue = (
        db.query(Issue)
        .filter(
            Issue.id == issue_id,
            (
                (Issue.reporter_id == current_user.id)
                | (Issue.assignee_id == current_user.id)
            )
        )
        .first()
    )

    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Issue not found or you do not have access "
                "to this issue."
            )
        )

    old_status = enum_value(issue.status)

    if issue.status in (
        IssueStatus.QA_VERIFICATION,
        IssueStatus.RESOLVED,
        IssueStatus.CLOSED
    ):
        return {
            "success": True,
            "message": (
                "Issue is already in QA verification "
                "or completed."
            ),
            "issue_id": issue.id,
            "status": old_status,
            "commit_hash": payload.commit_hash,
            "user_id": current_user.id
        }

    issue.status = IssueStatus.QA_VERIFICATION

    audit = AuditLog(
        issue_id=issue.id,
        user_id=current_user.id,
        action="GIT_WEBHOOK",
        field_name="status",
        old_value=old_status,
        new_value="QA_VERIFICATION"
    )

    db.add(audit)
    db.commit()
    db.refresh(issue)

    return {
        "success": True,
        "message": (
            f"Issue #{issue.id} moved to QA verification."
        ),
        "issue_id": issue.id,
        "status": enum_value(issue.status),
        "commit_hash": payload.commit_hash,
        "user_id": current_user.id
    }
