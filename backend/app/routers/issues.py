from datetime import datetime
from enum import Enum
from typing import Optional
from difflib import SequenceMatcher
import re

from app.services.developer_matcher import recommend_developers

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.database.database import get_db

from app.models.issue import (
    Issue,
    IssueStatus,
    Priority,
    Severity
)

from app.models.project import Project
from app.models.bug_category import BugCategory
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.services.notification_manager import notification_manager

from app.schemas.issue import (
    IssueCreate,
    IssueResponse,
    IssueStatusUpdate,
    IssueAssignment,
    IssueUpdate,
)

from pydantic import BaseModel


# ============================================================
# TRIAGE RECOMMENDATION REQUEST
# ============================================================

class TriageRecommendationRequest(BaseModel):
    title: str
    description: str


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/issues",
    tags=["Issues"]
)


# ============================================================
# DUPLICATE DETECTION
# ============================================================

def normalize_title(title: str) -> str:
    """
    Normalize an issue title for duplicate comparison.
    """

    if not title:
        return ""

    title = title.lower().strip()

    # Remove special characters
    title = re.sub(
        r"[^a-z0-9\s]",
        " ",
        title
    )

    # Remove extra spaces
    title = re.sub(
        r"\s+",
        " ",
        title
    )

    return title.strip()


def calculate_title_similarity(
    title1: str,
    title2: str
) -> float:
    """
    Calculate similarity between two issue titles.

    Returns a value between 0 and 1.
    """

    normalized_title1 = normalize_title(title1)
    normalized_title2 = normalize_title(title2)

    if not normalized_title1 or not normalized_title2:
        return 0.0

    return SequenceMatcher(
        None,
        normalized_title1,
        normalized_title2
    ).ratio()


def find_duplicate_issue(
    db: Session,
    project_id: int,
    title: str
):
    """
    Search for a possible duplicate issue
    inside the same project.

    Duplicate conditions:

    1. Exact normalized title match
    2. Title similarity >= 80%
    """

    normalized_title = normalize_title(title)

    if not normalized_title:
        return None

    existing_issues = (
        db.query(Issue)
        .filter(
            Issue.project_id == project_id
        )
        .all()
    )

    for existing_issue in existing_issues:

        existing_title = normalize_title(
            existing_issue.title
        )

        # Exact match
        if normalized_title == existing_title:
            return existing_issue

        # Similar title
        similarity = calculate_title_similarity(
            normalized_title,
            existing_title
        )

        if similarity >= 0.80:
            return existing_issue

    return None


# ============================================================
# SMART PRIORITY CALCULATOR
# ============================================================

def get_severity_weight(severity) -> int:
    """
    Convert severity into a numerical weight.
    """

    severity_value = (
        severity.value
        if isinstance(severity, Enum)
        else str(severity)
    )

    severity_weights = {
        "CRITICAL": 4,
        "MAJOR": 3,
        "MINOR": 2,
        "TRIVIAL": 1,
    }

    return severity_weights.get(
        severity_value.upper(),
        1
    )


def get_urgency_weight(urgency) -> int:
    """
    Convert category urgency into a numerical weight.
    """

    if urgency is None:
        return 1

    urgency_value = (
        urgency.value
        if isinstance(urgency, Enum)
        else str(urgency)
    )

    urgency_weights = {
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
    }

    return urgency_weights.get(
        urgency_value.upper(),
        1
    )


def calculate_priority_score(
    severity,
    urgency
) -> int:
    """
    Priority Score =
    Severity Weight × Category Urgency Weight
    """

    severity_weight = get_severity_weight(
        severity
    )

    urgency_weight = get_urgency_weight(
        urgency
    )

    return severity_weight * urgency_weight


def calculate_priority(
    priority_score: int
):
    """
    Convert priority score into priority level.

    9-12 -> URGENT
    6-8  -> HIGH
    3-5  -> MEDIUM
    1-2  -> LOW
    """

    if priority_score >= 10:
        return Priority.URGENT

    elif priority_score >= 7:
        return Priority.HIGH

    elif priority_score >= 4:
        return Priority.MEDIUM

    else:
        return Priority.LOW


# ============================================================
# CREATE ISSUE
# ============================================================

@router.post(
    "/",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_issue(
    issue_data: IssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new issue.

    Reporter is automatically taken from
    the authenticated user.

    Priority is automatically calculated.
    """

    # --------------------------------------------------------
    # Check project
    # --------------------------------------------------------

    project = (
        db.query(Project)
        .filter(
            Project.project_id == issue_data.project_id
        )
        .first()
    )

    if not project:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # --------------------------------------------------------
    # Check category
    # --------------------------------------------------------

    category = (
        db.query(BugCategory)
        .filter(
            BugCategory.category_id
            == issue_data.category_id
        )
        .first()
    )

    if not category:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bug category not found"
        )

    # --------------------------------------------------------
    # Duplicate detection
    # --------------------------------------------------------

    duplicate_issue = find_duplicate_issue(
        db=db,
        project_id=issue_data.project_id,
        title=issue_data.title
    )

    if duplicate_issue:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Possible duplicate issue found: "
                f"#{duplicate_issue.id} - "
                f"{duplicate_issue.title}"
            )
        )

    # --------------------------------------------------------
    # Check assignee
    # --------------------------------------------------------

    if issue_data.assignee_id is not None:

        assignee = (
            db.query(User)
            .filter(
                User.id == issue_data.assignee_id
            )
            .first()
        )

        if not assignee:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee not found"
            )

        if not assignee.is_active:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Cannot assign issue "
                    "to an inactive user"
                )
            )

        if assignee.role != "DEVELOPER":

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Issues can only be assigned "
                    "to DEVELOPER users"
                )
            )

    # ========================================================
    # SMART PRIORITY
    # ========================================================

    priority_score = calculate_priority_score(
        severity=issue_data.severity,
        urgency=category.urgency
    )

    calculated_priority = calculate_priority(
        priority_score
    )

    # --------------------------------------------------------
    # Create issue
    # --------------------------------------------------------

    new_issue = Issue(

        project_id=issue_data.project_id,

        reporter_id=current_user.id,

        assignee_id=issue_data.assignee_id,

        category_id=issue_data.category_id,

        sprint_id=issue_data.sprint_id,

        title=issue_data.title,

        description=issue_data.description,

        reproduction_steps=(
            issue_data.reproduction_steps
        ),

        severity=issue_data.severity,

        priority=calculated_priority,

        status=IssueStatus.REPORTED,

        dev_stage=issue_data.dev_stage,

        affected_modules=(
            issue_data.affected_modules
        ),

        environment_details=(
            issue_data.environment_details
        ),

        estimated_effort=(
            issue_data.estimated_effort
        ),

        priority_score=priority_score
    )

    # --------------------------------------------------------
    # Save issue
    # --------------------------------------------------------

    db.add(new_issue)

    db.commit()

    db.refresh(new_issue)

    # --------------------------------------------------------
    # Create ADMIN notifications
    # --------------------------------------------------------

    admins = (
        db.query(User)
        .filter(
            User.role == "ADMIN",
            User.is_active == True
        )
        .all()
    )

    for admin in admins:

        notification = Notification(
            user_id=admin.id,
            notification_type="NEW_ISSUE",
            title="New issue reported",
            message=(
                f"{current_user.full_name} reported "
                f"issue #{new_issue.id}: "
                f"{new_issue.title}"
            ),
            issue_id=new_issue.id,
            is_read=False,
            is_deleted=False
        )

        db.add(notification)

        # Send real-time notification to connected Admin
        await notification_manager.send_to_user(
            admin.id,
            {
                "type": "NEW_ISSUE",
                "notification_id": notification.id,
                "issue_id": new_issue.id,
                "title": "New issue reported",
                "message": (
                    f"{current_user.full_name} reported "
                    f"issue #{new_issue.id}: "
                    f"{new_issue.title}"
                ),
                "is_read": False
            }
        )

    db.commit()

    return new_issue


# ============================================================
# GET MY ISSUES
# ============================================================

@router.get(
    "/my",
    response_model=list[IssueResponse]
)
def get_my_issues(
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of issues to skip"
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of issues to return"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all issues:

    - Reported by the current user
    OR
    - Assigned to the current user
    """

    issues = (
        db.query(Issue)
        .filter(
            (Issue.reporter_id == current_user.id)
            |
            (Issue.assignee_id == current_user.id)
        )
        .order_by(
            Issue.created_at.desc()
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    return issues


# ============================================================
# GET ALL ISSUES - ADMIN
# ============================================================

@router.get(
    "/",
    response_model=list[IssueResponse]
)
def get_all_issues(
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of issues to skip"
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of issues to return"
    ),
    status_filter: Optional[IssueStatus] = Query(
        default=None,
        alias="status"
    ),

    severity: Optional[Severity] = Query(
        default=None
    ),

    priority: Optional[Priority] = Query(
        default=None
    ),

    category_id: Optional[int] = Query(
        default=None
    ),

    assignee_id: Optional[int] = Query(
        default=None
    ),

    project_id: Optional[int] = Query(
        default=None
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(require_admin)
):
    """
    Get all issues.

    ADMIN only.

    Supports filtering by:
    - Status
    - Severity
    - Priority
    - Category
    - Assignee
    - Project
    """

    query = db.query(Issue)

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    if status_filter is not None:

        query = query.filter(
            Issue.status == status_filter
        )

    # --------------------------------------------------------
    # Severity
    # --------------------------------------------------------

    if severity is not None:

        query = query.filter(
            Issue.severity == severity
        )

    # --------------------------------------------------------
    # Priority
    # --------------------------------------------------------

    if priority is not None:

        query = query.filter(
            Issue.priority == priority
        )

    # --------------------------------------------------------
    # Category
    # --------------------------------------------------------

    if category_id is not None:

        query = query.filter(
            Issue.category_id == category_id
        )

    # --------------------------------------------------------
    # Assignee
    # --------------------------------------------------------

    if assignee_id is not None:

        query = query.filter(
            Issue.assignee_id == assignee_id
        )

    # --------------------------------------------------------
    # Project
    # --------------------------------------------------------

    if project_id is not None:

        query = query.filter(
            Issue.project_id == project_id
        )

    # --------------------------------------------------------
    # Newest first
    # --------------------------------------------------------

    issues = (
        query
        .order_by(
            Issue.created_at.desc()
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    return issues


# ============================================================
# GET ISSUE BY ID
# ============================================================

@router.get(
    "/{issue_id}",
    response_model=IssueResponse
)
def get_issue_by_id(
    issue_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):
    """
    Get a specific issue.

    Access:
    - ADMIN
    - Reporter
    - Assignee
    """

    issue = (
        db.query(Issue)
        .filter(
            Issue.id == issue_id
        )
        .first()
    )

    if not issue:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )

    # --------------------------------------------------------
    # Access control
    # --------------------------------------------------------

    if (
        current_user.role != "ADMIN"
        and issue.reporter_id != current_user.id
        and issue.assignee_id != current_user.id
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have access "
                "to this issue"
            )
        )

    return issue


# ============================================================
# UPDATE ISSUE STATUS
# ============================================================

@router.patch(
    "/{issue_id}/status",
    response_model=IssueResponse
)
def update_issue_status(
    issue_id: int,

    status_data: IssueStatusUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):
    """
    Update issue status according to the workflow
    and role-based permissions.
    """

    issue = (
        db.query(Issue)
        .filter(
            Issue.id == issue_id
        )
        .first()
    )

    if not issue:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )

    # --------------------------------------------------------
    # Valid workflow
    # --------------------------------------------------------

    valid_transitions = {

        IssueStatus.REPORTED: [
            IssueStatus.TRIAGED
        ],

        IssueStatus.TRIAGED: [
            IssueStatus.IN_PROGRESS
        ],

        IssueStatus.IN_PROGRESS: [
            IssueStatus.CODE_REVIEW
        ],

        IssueStatus.CODE_REVIEW: [
            IssueStatus.QA_VERIFICATION
        ],

        IssueStatus.QA_VERIFICATION: [
            IssueStatus.RESOLVED
        ],

        IssueStatus.RESOLVED: [
            IssueStatus.CLOSED
        ],

        IssueStatus.CLOSED: []
    }

    current_status = issue.status

    new_status = status_data.status

    # --------------------------------------------------------
    # Same status
    # --------------------------------------------------------

    if current_status == new_status:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Issue is already in this status"
        )

    # --------------------------------------------------------
    # Validate workflow
    # --------------------------------------------------------

    if new_status not in valid_transitions[current_status]:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid status transition: "
                f"{current_status.value} -> "
                f"{new_status.value}"
            )
        )

    # ========================================================
    # ROLE-BASED STATUS PERMISSIONS
    # ========================================================

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if current_user.role == "ADMIN":

        pass

    # --------------------------------------------------------
    # REPORTED -> TRIAGED
    # ADMIN / TRIAGER
    # --------------------------------------------------------

    elif (
        current_status == IssueStatus.REPORTED
        and new_status == IssueStatus.TRIAGED
    ):

        if current_user.role not in [
            "ADMIN",
            "TRIAGER"
        ]:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only ADMIN or TRIAGER can "
                    "triage an issue"
                )
            )

    # --------------------------------------------------------
    # TRIAGED -> IN_PROGRESS
    #
    # IN_PROGRESS -> CODE_REVIEW
    #
    # Assigned DEVELOPER only
    # --------------------------------------------------------

    elif (
        current_status in [
            IssueStatus.TRIAGED,
            IssueStatus.IN_PROGRESS
        ]
        and new_status in [
            IssueStatus.IN_PROGRESS,
            IssueStatus.CODE_REVIEW
        ]
    ):

        if current_user.role != "DEVELOPER":

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only the assigned DEVELOPER "
                    "can update this development status"
                )
            )

        if issue.assignee_id != current_user.id:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only the assigned DEVELOPER "
                    "can update this issue"
                )
            )

    # --------------------------------------------------------
    # CODE_REVIEW -> QA_VERIFICATION
    #
    # DEVELOPER only
    # --------------------------------------------------------

    elif (
        current_status == IssueStatus.CODE_REVIEW
        and new_status == IssueStatus.QA_VERIFICATION
    ):

        if current_user.role != "DEVELOPER":

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only a DEVELOPER can submit "
                    "an issue for QA verification"
                )
            )

        if issue.assignee_id != current_user.id:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only the assigned DEVELOPER "
                    "can submit this issue for QA"
                )
            )

    # --------------------------------------------------------
    # QA_VERIFICATION -> RESOLVED
    #
    # TESTER only
    # --------------------------------------------------------

    elif (
        current_status == IssueStatus.QA_VERIFICATION
        and new_status == IssueStatus.RESOLVED
    ):

        if current_user.role != "TESTER":

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only a TESTER can verify "
                    "and resolve an issue"
                )
            )

    # --------------------------------------------------------
    # RESOLVED -> CLOSED
    #
    # ADMIN / TRIAGER
    # --------------------------------------------------------

    elif (
        current_status == IssueStatus.RESOLVED
        and new_status == IssueStatus.CLOSED
    ):

        if current_user.role not in [
            "ADMIN",
            "TRIAGER"
        ]:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only ADMIN or TRIAGER can "
                    "close an issue"
                )
            )

    # --------------------------------------------------------
    # Update status
    # --------------------------------------------------------

    issue.status = new_status

    # --------------------------------------------------------
    # Set resolved timestamp
    # --------------------------------------------------------

    if new_status == IssueStatus.RESOLVED:

        issue.resolved_at = datetime.utcnow()

    # --------------------------------------------------------
    # Audit log for status change
    # --------------------------------------------------------

    audit_log = AuditLog(
        issue_id=issue.id,
        user_id=current_user.id,
        action="STATUS_CHANGED",
        field_name="status",
        old_value=current_status.value,
        new_value=new_status.value,
    )

    db.add(audit_log)

    # --------------------------------------------------------
    # Save status change
    # --------------------------------------------------------

    db.commit()

    db.refresh(issue)

    return issue


# ============================================================
# ASSIGN ISSUE
# ============================================================

@router.patch(
    "/{issue_id}/assign",
    response_model=IssueResponse
)
async def assign_issue(
    issue_id: int,
    assignment_data: IssueAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Assign an issue to an active DEVELOPER.

    Only ADMIN users can assign issues.
    """

    # --------------------------------------------------------
    # Check issue
    # --------------------------------------------------------

    issue = (
        db.query(Issue)
        .filter(
            Issue.id == issue_id
        )
        .first()
    )

    if not issue:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )

    # --------------------------------------------------------
    # ADMIN permission
    # --------------------------------------------------------

    if current_user.role != "ADMIN":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign issues"
        )

    # --------------------------------------------------------
    # Find assignee
    # --------------------------------------------------------

    assignee = (
        db.query(User)
        .filter(
            User.id == assignment_data.assignee_id
        )
        .first()
    )

    if not assignee:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignee not found"
        )

    # --------------------------------------------------------
    # Active user
    # --------------------------------------------------------

    if not assignee.is_active:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Cannot assign issue "
                "to an inactive user"
            )
        )

    # --------------------------------------------------------
    # DEVELOPER only
    # --------------------------------------------------------

    if assignee.role != "DEVELOPER":

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only DEVELOPER users "
                "can be assigned to issues"
            )
        )

    # --------------------------------------------------------
    # Prevent duplicate assignment
    # --------------------------------------------------------

    old_assignee_id = issue.assignee_id

    if old_assignee_id == assignee.id:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Issue is already assigned "
                "to this user"
            )
        )

    # --------------------------------------------------------
    # Assign issue
    # --------------------------------------------------------

    issue.assignee_id = assignee.id

    # --------------------------------------------------------
    # Audit log
    # --------------------------------------------------------

    audit_log = AuditLog(
        issue_id=issue.id,
        user_id=current_user.id,
        action="ASSIGNED",
        field_name="assignee_id",
        old_value=(
            str(old_assignee_id)
            if old_assignee_id is not None
            else None
        ),
        new_value=str(assignee.id)
    )

    db.add(audit_log)

    # --------------------------------------------------------
    # Create notification for assigned developer
    # --------------------------------------------------------

    notification = Notification(
        user_id=assignee.id,
        notification_type="ISSUE_ASSIGNED",
        title="Issue assigned to you",
        message=(
            f"Admin {current_user.full_name} assigned "
            f"issue #{issue.id}: {issue.title} "
            f"to you."
        ),
        issue_id=issue.id,
        is_read=False,
        is_deleted=False
    )

    db.add(notification)

    # --------------------------------------------------------
    # Flush assignment and notification
    # --------------------------------------------------------

    db.flush()

    # --------------------------------------------------------
    # Prepare real-time notification payload
    # --------------------------------------------------------

    notification_payload = {
        "type": "ISSUE_ASSIGNED",
        "notification_id": notification.id,
        "issue_id": issue.id,
        "title": notification.title,
        "message": notification.message,
        "is_read": False
    }

    # --------------------------------------------------------
    # Commit assignment, audit log and notification
    # --------------------------------------------------------

    db.commit()

    # --------------------------------------------------------
    # Refresh issue from PostgreSQL
    # --------------------------------------------------------

    db.refresh(issue)

    # --------------------------------------------------------
    # Send real-time notification after successful commit
    # --------------------------------------------------------

    await notification_manager.send_to_user(
        assignee.id,
        notification_payload
    )

    return issue


# ============================================================
# UPDATE ISSUE
# ============================================================

@router.patch(
    "/{issue_id}",
    response_model=IssueResponse
)
def update_issue(
    issue_id: int,

    issue_data: IssueUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):
    """
    Update an existing issue.

    Every changed field is recorded
    in the audit log.

    If severity or category changes,
    Smart Priority is recalculated automatically.

    Manual priority override is allowed
    only for ADMIN and TRIAGER.
    """

    # --------------------------------------------------------
    # Find issue
    # --------------------------------------------------------

    issue = (
        db.query(Issue)
        .filter(
            Issue.id == issue_id
        )
        .first()
    )

    if not issue:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )

    # --------------------------------------------------------
    # Access
    # --------------------------------------------------------

    if (
        current_user.role != "ADMIN"
        and issue.reporter_id != current_user.id
        and issue.assignee_id != current_user.id
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to update this issue"
            )
        )

    # --------------------------------------------------------
    # Get provided fields
    # --------------------------------------------------------

    update_data = issue_data.model_dump(
        exclude_unset=True
    )

    # --------------------------------------------------------
    # No fields
    # --------------------------------------------------------

    if not update_data:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )

    # ========================================================
    # PRIORITY OVERRIDE PERMISSION
    # ========================================================

    if "priority" in update_data:

        if current_user.role not in [
            "ADMIN",
            "TRIAGER"
        ]:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only ADMIN or TRIAGER can "
                    "manually override priority"
                )
            )

    # ========================================================
    # VALIDATE CATEGORY
    # ========================================================

    if "category_id" in update_data:

        new_category = (
            db.query(BugCategory)
            .filter(
                BugCategory.category_id
                == update_data["category_id"]
            )
            .first()
        )

        if not new_category:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bug category not found"
            )

    else:

        new_category = (
            db.query(BugCategory)
            .filter(
                BugCategory.category_id
                == issue.category_id
            )
            .first()
        )

        if not new_category:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Current bug category not found"
            )

    # ========================================================
    # DETERMINE SEVERITY
    # ========================================================

    if "severity" in update_data:

        new_severity = update_data["severity"]

    else:

        new_severity = issue.severity

    # ========================================================
    # SMART PRIORITY RECALCULATION
    # ========================================================

    if (
        (
            "severity" in update_data
            or "category_id" in update_data
        )
        and "priority" not in update_data
    ):

        priority_score = calculate_priority_score(
            severity=new_severity,
            urgency=new_category.urgency
        )

        calculated_priority = calculate_priority(
            priority_score
        )

        update_data["priority_score"] = priority_score

        update_data["priority"] = calculated_priority

    # ========================================================
    # UPDATE + AUDIT LOG
    # ========================================================

    for field_name, new_value in update_data.items():

        old_value = getattr(
            issue,
            field_name
        )

        # ----------------------------------------------------
        # Convert old enum to string
        # ----------------------------------------------------

        if isinstance(
            old_value,
            Enum
        ):

            old_value = old_value.value

        # ----------------------------------------------------
        # Convert new enum to string
        # ----------------------------------------------------

        if isinstance(
            new_value,
            Enum
        ):

            new_value = new_value.value

        # ----------------------------------------------------
        # No actual change
        # ----------------------------------------------------

        if old_value == new_value:

            continue

        # ----------------------------------------------------
        # Update issue
        # ----------------------------------------------------

        setattr(
            issue,
            field_name,
            new_value
        )

        # ----------------------------------------------------
        # Audit log
        # ----------------------------------------------------

        audit_log = AuditLog(

            issue_id=issue.id,

            user_id=current_user.id,

            action="UPDATED",

            field_name=field_name,

            old_value=(
                str(old_value)
                if old_value is not None
                else None
            ),

            new_value=(
                str(new_value)
                if new_value is not None
                else None
            )
        )

        db.add(audit_log)

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    db.commit()

    db.refresh(issue)

    return issue


# ============================================================
# SMART DEVELOPER MATCHER / TRIAGE RECOMMENDATION
# ============================================================

@router.post("/triage-recommendation")
def get_triage_recommendation(
    request: TriageRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze an issue and recommend the top 3 developers.
    """

    recommendations = recommend_developers(
        db=db,
        title=request.title,
        description=request.description,
    )

    return {
        "title": request.title,
        "description": request.description,
        "recommended_developers": recommendations,
    }