from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.issue import Issue
from app.services.resolution_service import generate_resolution_assistance

# Use the same authentication dependency
# that your existing issue routers use.
from app.auth.dependencies import get_current_user


router = APIRouter(
    prefix="/api/v1/resolution-assistance",
    tags=["Resolution Assistance"]
)


@router.get("/{issue_id}")
def get_resolution_assistance(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Generate resolution assistance for a user's issue.
    """

    # --------------------------------------------------------
    # Find issue
    # --------------------------------------------------------

    issue = (
        db.query(Issue)
        .filter(Issue.id == issue_id)
        .first()
    )

    if not issue:

        raise HTTPException(
            status_code=404,
            detail="Issue not found."
        )


    # --------------------------------------------------------
    # Security:
    # Make sure the user owns the issue
    # --------------------------------------------------------

    if issue.reporter_id != current_user.id:

        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access this issue."
        )


    # --------------------------------------------------------
    # Generate assistance
    # --------------------------------------------------------

    result = generate_resolution_assistance(
        db=db,
        issue=issue
    )


    return result