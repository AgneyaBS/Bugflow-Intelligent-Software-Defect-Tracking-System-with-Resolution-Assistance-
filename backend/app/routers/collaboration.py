from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.database import get_db

from fastapi.responses import StreamingResponse
from app.services.report_service import generate_issue_report

from app.models.comment import Comment
from app.models.attachment import Attachment
from app.models.issue import Issue
from app.models.user import User
from app.models.audit_log import AuditLog

from app.schemas.comment import CommentCreate, CommentResponse


router = APIRouter(
    prefix="/api/v1/collaboration",
    tags=["Collaboration"]
)


# ============================================================
# ADD COMMENT
# ============================================================

@router.post(
    "/issues/{issue_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED
)
def add_comment(
    issue_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a comment to an issue.
    """

    issue = (
        db.query(Issue)
        .filter(Issue.id == issue_id)
        .first()
    )

    if not issue:
        raise HTTPException(
            status_code=404,
            detail="Issue not found"
        )

    comment = Comment(
        issue_id=issue_id,
        user_id=current_user.id,
        comment_text=comment_data.comment_text,
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


# ============================================================
# GET COMMENTS
# ============================================================

@router.get(
    "/issues/{issue_id}/comments",
    response_model=list[CommentResponse]
)
def get_comments(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all comments for an issue.
    """

    issue = (
        db.query(Issue)
        .filter(Issue.id == issue_id)
        .first()
    )

    if not issue:
        raise HTTPException(
            status_code=404,
            detail="Issue not found"
        )

    comments = (
        db.query(Comment)
        .filter(Comment.issue_id == issue_id)
        .order_by(Comment.created_at.asc())
        .all()
    )

    return comments
# ============================================================
# FILE ATTACHMENT UPLOAD
# ============================================================

@router.post(
    "/issues/{issue_id}/attachments",
    status_code=status.HTTP_201_CREATED
)
def upload_attachment(
    issue_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload an attachment to an issue.
    Allowed file types: PNG, JPG, LOG
    """

    # --------------------------------------------------------
    # Check whether issue exists
    # --------------------------------------------------------

    issue = (
        db.query(Issue)
        .filter(Issue.id == issue_id)
        .first()
    )

    if not issue:
        raise HTTPException(
            status_code=404,
            detail="Issue not found"
        )

    # --------------------------------------------------------
    # Validate file extension
    # --------------------------------------------------------

    allowed_extensions = {".png", ".jpg", ".log"}

    file_name = file.filename or ""
    extension = ""

    if "." in file_name:
        extension = "." + file_name.rsplit(".", 1)[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only .png, .jpg, and .log files are allowed"
        )

    # --------------------------------------------------------
    # Create uploads directory
    # --------------------------------------------------------

    import os

    upload_directory = "uploads"
    os.makedirs(upload_directory, exist_ok=True)

    # --------------------------------------------------------
    # Save file
    # --------------------------------------------------------

    file_path = os.path.join(
        upload_directory,
        file_name
    )

    contents = file.file.read()

    with open(file_path, "wb") as output_file:
        output_file.write(contents)

    # --------------------------------------------------------
    # Save attachment information in database
    # --------------------------------------------------------

    attachment = Attachment(
        issue_id=issue_id,
        user_id=current_user.id,
        file_name=file_name,
        file_path=file_path,
        file_type=file.content_type or "application/octet-stream",
    )

    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return {
        "message": "File uploaded successfully",
        "attachment_id": attachment.id,
        "issue_id": attachment.issue_id,
        "file_name": attachment.file_name,
        "file_type": attachment.file_type,
        "file_path": attachment.file_path,
        "uploaded_by": current_user.id,
        "uploaded_at": attachment.uploaded_at,
    }
    # ============================================================
# LIVE ACTIVITY STREAM
# ============================================================

@router.get("/activity")
def get_live_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return recent audit activities for the
    currently logged-in user's issues.
    """

    activities = (
        db.query(AuditLog)
        .join(
            Issue,
            AuditLog.issue_id == Issue.id
        )
        .filter(
            Issue.reporter_id == current_user.id
        )
        .order_by(
            AuditLog.timestamp.desc()
        )
        .limit(10)
        .all()
    )

    result = []

    for activity in activities:

        result.append({
            "id": activity.id,
            "issue_id": activity.issue_id,
            "user_id": activity.user_id,
            "action": activity.action,
            "field_name": activity.field_name,
            "old_value": activity.old_value,
            "new_value": activity.new_value,
            "timestamp": activity.timestamp
        })

    return result
# ============================================================
# PDF ISSUE REPORT
# ============================================================

@router.get("/report/pdf")
def generate_pdf_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a PDF report for the currently
    logged-in user's reported issues.
    """

    issues = (
        db.query(Issue)
        .filter(
            Issue.reporter_id == current_user.id
        )
        .order_by(
            Issue.created_at.desc()
        )
        .all()
    )

    pdf_buffer = generate_issue_report(issues)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                "attachment; filename=bugflow_issue_report.pdf"
        }
    )
    # ============================================================
# PROJECT BACKLOG
# ============================================================

@router.get("/backlog")
def get_backlog_issues(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return issues that are not assigned to any sprint.

    These issues form the project backlog.
    """

    backlog_issues = (
        db.query(Issue)
        .filter(
            Issue.sprint_id.is_(None)
        )
        .order_by(
            Issue.created_at.desc()
        )
        .all()
    )

    return backlog_issues