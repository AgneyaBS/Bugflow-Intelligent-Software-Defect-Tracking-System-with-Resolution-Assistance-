import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.issue import Issue, IssueStatus
from app.models.audit_log import AuditLog
from app.models.user import User


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Webhooks"]
)


# ============================================================
# GIT WEBHOOK REQUEST
# ============================================================

class GitWebhookRequest(BaseModel):
    message: str
    commit_hash: str | None = None

# ============================================================
# GET ALL ISSUES FOR WEBHOOK SIMULATOR
# ============================================================

@router.get("/issues")
def get_webhook_issues(
    db: Session = Depends(get_db)
):
    """
    Return all issues for the CI/CD webhook simulator.

    Includes:
    - REPORTED
    - IN_PROGRESS
    - QA_VERIFICATION
    - RESOLVED
    - CLOSED
    - Newly created issues
    """

    issues = (
        db.query(Issue)
        .order_by(Issue.id.asc())
        .all()
    )

    return [
        {
            "id": issue.id,
            "title": issue.title,
            "status": issue.status.value if issue.status else "UNKNOWN"
        }
        for issue in issues
    ]
# ============================================================
# GIT WEBHOOK
# ============================================================

@router.post("/git")
def git_webhook(
    webhook_data: GitWebhookRequest,
    db: Session = Depends(get_db)
):
    """
    Process a Git commit message.

    Supported keywords:
    - fixes #2
    - closes #5
    - resolves #8

    Matching issues are automatically moved
    to QA_VERIFICATION.
    """

    # --------------------------------------------------------
    # Find bug references in commit message
    # --------------------------------------------------------

    pattern = r"\b(?:fixes|closes|resolves)\s+#(\d+)\b"

    matches = re.findall(
        pattern,
        webhook_data.message,
        flags=re.IGNORECASE
    )

    # --------------------------------------------------------
    # No bug reference found
    # --------------------------------------------------------

    if not matches:
        return {
            "success": True,
            "message": "No bug references found in commit message.",
            "updated_issues": []
        }

    # --------------------------------------------------------
    # Remove duplicate issue IDs
    # --------------------------------------------------------

    issue_ids = list(
        dict.fromkeys(
            int(issue_id)
            for issue_id in matches
        )
    )

    updated_issues = []

    # --------------------------------------------------------
    # Find system/admin user for audit log
    # --------------------------------------------------------

    system_user = (
        db.query(User)
        .filter(
            User.role == "ADMIN",
            User.is_active == True
        )
        .order_by(User.id.asc())
        .first()
    )

    if not system_user:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No active ADMIN user available for system audit logging."
        )

    # --------------------------------------------------------
    # Process each referenced issue
    # --------------------------------------------------------

    for issue_id in issue_ids:

        issue = (
            db.query(Issue)
            .filter(
                Issue.id == issue_id
            )
            .first()
        )

        # ----------------------------------------------------
        # Issue does not exist
        # ----------------------------------------------------

        if not issue:
            continue

        # ----------------------------------------------------
        # Already in QA or later
        # ----------------------------------------------------

        if issue.status in [
            IssueStatus.QA_VERIFICATION,
            IssueStatus.RESOLVED,
            IssueStatus.CLOSED
        ]:

            updated_issues.append({
                "issue_id": issue.id,
                "old_status": issue.status.value,
                "new_status": issue.status.value,
                "message": "Issue already passed development stage."
            })

            continue

        # ----------------------------------------------------
        # Save old status
        # ----------------------------------------------------

        old_status = issue.status

        # ----------------------------------------------------
        # Automatically move to QA
        # ----------------------------------------------------

        issue.status = IssueStatus.QA_VERIFICATION

        # ----------------------------------------------------
        # Commit description
        # ----------------------------------------------------

        commit_reference = (
            webhook_data.commit_hash
            if webhook_data.commit_hash
            else "unknown"
        )

        # ----------------------------------------------------
        # Audit log
        # ----------------------------------------------------

        audit_log = AuditLog(
            issue_id=issue.id,
            user_id=system_user.id,
            action=(
                f"Auto-transitioned by Git commit "
                f"#{commit_reference}"
            ),
            field_name="status",
            old_value=old_status.value,
            new_value=IssueStatus.QA_VERIFICATION.value
        )

        db.add(audit_log)

        # ----------------------------------------------------
        # Add response information
        # ----------------------------------------------------

        updated_issues.append({
            "issue_id": issue.id,
            "old_status": old_status.value,
            "new_status": IssueStatus.QA_VERIFICATION.value,
            "commit_hash": commit_reference
        })

    # --------------------------------------------------------
    # Save all changes
    # --------------------------------------------------------

    db.commit()

    return {
        "success": True,
        "message": "Git webhook processed successfully.",
        "updated_issues": updated_issues
    }