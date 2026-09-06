from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database.database import get_db
from app.models.user import User


router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)


# ============================================================
# GET ALL ACTIVE USERS - ADMIN ONLY
# ============================================================

@router.get("/")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get all active users.

    Only ADMIN users can access this endpoint.
    Used by the admin dashboard for issue assignment.
    """

    users = (
        db.query(User)
        .filter(User.is_active == True)
        .order_by(User.id.asc())
        .all()
    )

    return [
        {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at
            
        }
        for user in users
    ]