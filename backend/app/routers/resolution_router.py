from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.issue import Issue
from app.services.resolution_service import generate_resolution_assistance
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

    # ========================================================
    # FIND ISSUE
    # ========================================================

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

    # ========================================================
    # CURRENT USER
    # ========================================================

    current_user_id = current_user.id

    user_role = current_user.role

    if hasattr(user_role, "value"):
        user_role = user_role.value

    user_role = str(user_role).upper()

    # ========================================================
    # ACCESS CHECK
    # ========================================================

    is_admin = user_role == "ADMIN"

    is_reporter = (
        issue.reporter_id is not None
        and issue.reporter_id == current_user_id
    )

    is_assignee = (
        issue.assignee_id is not None
        and issue.assignee_id == current_user_id
    )

    access_allowed = (
        is_admin
        or is_reporter
        or is_assignee
    )

    # ========================================================
    # TERMINAL DEBUG
    # ========================================================

    print("\n")
    print("############################################")
    print("#       BUGFLOW RESOLUTION DEBUG           #")
    print("############################################")
    print("Issue ID        :", issue.id)
    print("Issue Title     :", issue.title)
    print("Reporter ID     :", issue.reporter_id)
    print("Assignee ID     :", issue.assignee_id)
    print("Current User ID :", current_user_id)
    print("Current Role    :", user_role)
    print("--------------------------------------------")
    print("Is Admin        :", is_admin)
    print("Is Reporter     :", is_reporter)
    print("Is Assignee     :", is_assignee)
    print("Access Allowed  :", access_allowed)
    print("############################################")
    print("\n")

    # ========================================================
    # TEMPORARY DIAGNOSTIC RESPONSE
    # ========================================================
    #
    # REMOVE THIS BLOCK AFTER WE FIND THE PROBLEM.
    #

    if not access_allowed:
        raise HTTPException(
            status_code=403,
            detail=(
                "DEBUG_403 | "
                f"issue_id={issue.id} | "
                f"reporter_id={issue.reporter_id} | "
                f"assignee_id={issue.assignee_id} | "
                f"current_user_id={current_user_id} | "
                f"role={user_role}"
            )
        )

    # ========================================================
    # GENERATE RESOLUTION
    # ========================================================

    try:

        result = generate_resolution_assistance(
            db=db,
            issue=issue
        )

        return result

    except HTTPException:
        raise

    except Exception as e:

        print("Resolution generation error:", str(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to generate resolution assistance."
        )