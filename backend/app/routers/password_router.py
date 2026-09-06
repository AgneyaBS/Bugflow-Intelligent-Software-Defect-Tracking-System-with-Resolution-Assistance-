from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.schemas.password_schema import ResetPasswordRequest
from app.auth.security import hash_password


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Password Reset"]
)


# ============================================================
# FORGOT PASSWORD
# ============================================================

@router.post("/forgot-password")
def forgot_password(
    email: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user:
        return {
            "message": (
                "If an account exists with this email, "
                "a password reset request has been created."
            )
        }

    token = secrets.token_urlsafe(32)

    expires_at = datetime.utcnow() + timedelta(minutes=15)

    user.reset_token = token
    user.reset_token_expires = expires_at

    db.commit()

    return {
        "message": "Password reset request created successfully.",
        "reset_token": token,
        "expires_in_minutes": 15
    }


# ============================================================
# RESET PASSWORD
# ============================================================

@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.reset_token == request.token
    ).first()

    if not user:
        return {
            "success": False,
            "message": "Invalid or expired reset token."
        }

    if (
        user.reset_token_expires is None
        or user.reset_token_expires < datetime.utcnow()
    ):
        user.reset_token = None
        user.reset_token_expires = None

        db.commit()

        return {
            "success": False,
            "message": "Invalid or expired reset token."
        }

    # Hash the new password
    user.hashed_password = hash_password(
        request.new_password
    )

    # Remove used reset token
    user.reset_token = None
    user.reset_token_expires = None

    db.commit()

    return {
        "success": True,
        "message": "Password reset successfully. You can now login."
    }