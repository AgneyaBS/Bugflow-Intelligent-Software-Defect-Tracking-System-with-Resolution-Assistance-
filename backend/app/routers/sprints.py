from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.issue import Issue
from app.models.sprint import Sprint
from app.auth.dependencies import get_current_user
from app.schemas.sprint import SprintCreate, SprintResponse


router = APIRouter(
    prefix="/api/v1/sprints",
    tags=["Sprints"]
)


# ============================================================
# CREATE SPRINT
# ============================================================

@router.post(
    "/",
    response_model=SprintResponse,
    status_code=status.HTTP_201_CREATED
)
def create_sprint(
    sprint_data: SprintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new sprint.
    """

    # --------------------------------------------------------
    # Validate dates
    # --------------------------------------------------------

    if sprint_data.end_date < sprint_data.start_date:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be before start date"
        )

    # --------------------------------------------------------
    # Create sprint
    # --------------------------------------------------------

    sprint = Sprint(
        name=sprint_data.name,
        goal=sprint_data.goal,
        start_date=sprint_data.start_date,
        end_date=sprint_data.end_date,
        status=sprint_data.status,
        velocity=0
    )

    db.add(sprint)

    db.commit()

    db.refresh(sprint)

    return sprint


# ============================================================
# GET ALL SPRINTS
# ============================================================

@router.get(
    "/",
    response_model=list[SprintResponse]
)
def get_sprints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all sprints.
    """

    sprints = (
        db.query(Sprint)
        .order_by(Sprint.id.desc())
        .all()
    )

    return sprints


# ============================================================
# ADD ISSUE TO SPRINT
# ============================================================

@router.post(
    "/{sprint_id}/add-issue/{issue_id}"
)
def add_issue_to_sprint(
    sprint_id: int,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add an issue from the backlog to a sprint.
    """

    # --------------------------------------------------------
    # Check sprint
    # --------------------------------------------------------

    sprint = (
        db.query(Sprint)
        .filter(Sprint.id == sprint_id)
        .first()
    )

    if not sprint:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found"
        )

    # --------------------------------------------------------
    # Check sprint status
    # --------------------------------------------------------

    if sprint.status == "COMPLETED":

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add an issue to a completed sprint"
        )

    # --------------------------------------------------------
    # Check issue
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Check whether issue is already assigned
    # --------------------------------------------------------

    if issue.sprint_id is not None:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Issue is already assigned to a sprint"
        )

    # --------------------------------------------------------
    # Assign issue to sprint
    # --------------------------------------------------------

    issue.sprint_id = sprint.id

    db.add(issue)

    db.commit()

    db.refresh(issue)

    # --------------------------------------------------------
    # Return response
    # --------------------------------------------------------

    return {
        "message": "Issue added to sprint successfully",
        "issue_id": issue.id,
        "sprint_id": issue.sprint_id
    }


# ============================================================
# COMPLETE SPRINT
# ============================================================

@router.post(
    "/{sprint_id}/complete"
)
def complete_sprint(
    sprint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Complete a sprint and calculate its velocity.

    Velocity = number of successfully resolved issues
    in the sprint.
    """

    # --------------------------------------------------------
    # Check sprint
    # --------------------------------------------------------

    sprint = (
        db.query(Sprint)
        .filter(Sprint.id == sprint_id)
        .first()
    )

    if not sprint:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found"
        )

    # --------------------------------------------------------
    # Check sprint status
    # --------------------------------------------------------

    if sprint.status == "COMPLETED":

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sprint is already completed"
        )

    # --------------------------------------------------------
    # Calculate velocity
    # --------------------------------------------------------

    resolved_issue_count = (
        db.query(Issue)
        .filter(
            Issue.sprint_id == sprint.id,
            Issue.status == "RESOLVED"
        )
        .count()
    )

    # --------------------------------------------------------
    # Update sprint
    # --------------------------------------------------------

    sprint.status = "COMPLETED"

    sprint.velocity = resolved_issue_count

    db.commit()

    db.refresh(sprint)

    # --------------------------------------------------------
    # Return response
    # --------------------------------------------------------

    return {
        "message": "Sprint completed successfully",
        "sprint_id": sprint.id,
        "status": sprint.status,
        "velocity": sprint.velocity
    }