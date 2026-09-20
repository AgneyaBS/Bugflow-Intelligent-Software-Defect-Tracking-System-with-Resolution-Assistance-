from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/api/v1/profile",
    tags=["Profile"]
)


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
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
# GET CURRENT PROFILE
# ============================================================

@router.get("/")
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    user = (
        db.query(User)
        .filter(User.id == current_user.id)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "team": user.team,
        "core_skills": user.core_skills,
        "proficiency": user.proficiency,
        "phone": user.phone,
        "department": user.department,
        "about": user.about,
        "profile_picture": user.profile_picture,
        "is_active": user.is_active,
        "created_at": user.created_at
    }


# ============================================================
# UPDATE CURRENT PROFILE
# ============================================================

@router.put("/")
def update_profile(
    profile_data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    user = (
        db.query(User)
        .filter(User.id == current_user.id)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


    # --------------------------------------------------------
    # Check username
    # --------------------------------------------------------

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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )


    # --------------------------------------------------------
    # Check email
    # --------------------------------------------------------

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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )


    # --------------------------------------------------------
    # Update profile
    # --------------------------------------------------------

    user.full_name = profile_data.full_name
    user.username = profile_data.username
    user.email = profile_data.email
    user.phone = profile_data.phone
    user.department = profile_data.department
    user.about = profile_data.about
    user.profile_picture = profile_data.profile_picture


    db.commit()
    db.refresh(user)


    return {
        "message": "Profile updated successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "team": user.team,
            "core_skills": user.core_skills,
            "proficiency": user.proficiency,
            "phone": user.phone,
            "department": user.department,
            "about": user.about,
            "profile_picture": user.profile_picture
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

    user = (
        db.query(User)
        .filter(User.id == current_user.id)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


    # --------------------------------------------------------
    # Verify current password
    # --------------------------------------------------------

    if not pwd_context.verify(
        password_data.current_password,
        user.hashed_password
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )


    # --------------------------------------------------------
    # Validate new password
    # --------------------------------------------------------

    if len(password_data.new_password) < 8:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least 8 characters"
        )


    # --------------------------------------------------------
    # Save new password
    # --------------------------------------------------------

    user.hashed_password = pwd_context.hash(
        password_data.new_password
    )

    db.commit()


    return {
        "message": "Password changed successfully"
    }