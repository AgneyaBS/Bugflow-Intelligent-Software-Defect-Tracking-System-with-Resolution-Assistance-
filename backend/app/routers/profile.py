from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import hash_password, verify_password
from app.database.database import get_db
from app.models.user import User


router = APIRouter(
    prefix="/api/v1/profile",
    tags=["Profile"]
)


# ============================================================
# PROFILE UPDATE SCHEMA
# ============================================================

class ProfileUpdate(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    phone: str | None = None
    department: str | None = None
    about: str | None = None
    profile_picture: str | None = None


# ============================================================
# PASSWORD CHANGE SCHEMA
# ============================================================

class PasswordChange(BaseModel):
    current_password: str
    new_password: str


# ============================================================
# GET CURRENT USER PROFILE
# ============================================================

@router.get("/")
def get_profile(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "team": current_user.team,
        "core_skills": current_user.core_skills,
        "proficiency": current_user.proficiency,
        "phone": current_user.phone,
        "department": current_user.department,
        "about": current_user.about,
        "profile_picture": current_user.profile_picture,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }


# ============================================================
# UPDATE CURRENT USER PROFILE
# ============================================================

@router.put("/")
def update_profile(
    profile_data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check username belongs to another user
    existing_username = (
        db.query(User)
        .filter(
            User.username == profile_data.username,
            User.id != current_user.id
        )
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Username already exists."
        )

    # Check email belongs to another user
    existing_email = (
        db.query(User)
        .filter(
            User.email == profile_data.email,
            User.id != current_user.id
        )
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already exists."
        )

    current_user.full_name = profile_data.full_name
    current_user.username = profile_data.username
    current_user.email = profile_data.email
    current_user.phone = profile_data.phone
    current_user.department = profile_data.department
    current_user.about = profile_data.about
    current_user.profile_picture = profile_data.profile_picture

    db.commit()
    db.refresh(current_user)

    return {
        "success": True,
        "message": "Profile updated successfully.",
        "profile": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "phone": current_user.phone,
            "department": current_user.department,
            "about": current_user.about,
            "profile_picture": current_user.profile_picture
        }
    }


# ============================================================
# CHANGE PASSWORD
# ============================================================

@router.put("/password")
def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(
        password_data.current_password,
        current_user.hashed_password
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect."
        )

    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="New password must contain at least 8 characters."
        )

    current_user.hashed_password = hash_password(
        password_data.new_password
    )

    db.commit()

    return {
        "success": True,
        "message": "Password changed successfully."
    }