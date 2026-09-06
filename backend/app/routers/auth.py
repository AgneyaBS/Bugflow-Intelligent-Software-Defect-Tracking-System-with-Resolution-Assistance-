from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token
)
from app.database.database import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    TokenResponse
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


# ============================================================
# REGISTER USER
# ============================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new BugFlow user.
    """

    # --------------------------------------------------------
    # Check duplicate username
    # --------------------------------------------------------

    existing_username = (
        db.query(User)
        .filter(User.username == user_data.username)
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

    # --------------------------------------------------------
    # Check duplicate email
    # --------------------------------------------------------

    existing_email = (
        db.query(User)
        .filter(User.email == str(user_data.email))
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # --------------------------------------------------------
    # Public registration cannot create ADMIN
    # --------------------------------------------------------

    allowed_public_roles = {
        "DEVELOPER",
        "TESTER",
        "TRIAGER",
        "STAKEHOLDER"
    }

    requested_role = user_data.role.upper()

    if requested_role not in allowed_public_roles:
        requested_role = "TESTER"

    # --------------------------------------------------------
    # Create user
    # --------------------------------------------------------

    new_user = User(
        username=user_data.username,
        email=str(user_data.email),
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=requested_role,
        team=user_data.team,
        core_skills=user_data.core_skills,
        proficiency=user_data.proficiency,
        is_active=True
    )

    # --------------------------------------------------------
    # Save user to PostgreSQL
    # --------------------------------------------------------

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
# ============================================================
# LOGIN USER
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse
)
def login_user(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate a BugFlow user using
    username OR email and password.
    """

    # --------------------------------------------------------
    # Find user by username OR email
    # --------------------------------------------------------

    user = (
        db.query(User)
        .filter(
            (User.username == login_data.identifier) |
            (User.email == login_data.identifier)
        )
        .first()
    )

    # --------------------------------------------------------
    # Validate user and password
    # --------------------------------------------------------

    if not user or not verify_password(
        login_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    # --------------------------------------------------------
    # Check account status
    # --------------------------------------------------------

    if not user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # --------------------------------------------------------
    # Create JWT
    # --------------------------------------------------------

    access_token = create_access_token(
        user_id=user.id,
        role=user.role
    )

    # --------------------------------------------------------
    # Return token + user
    # --------------------------------------------------------

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }