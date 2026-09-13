from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.auth.security import hash_password
from app.database.database import get_db
from app.models.user import User


router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)


# ============================================================
# CREATE USER / DEVELOPER SCHEMA
# ============================================================

class UserCreateRequest(BaseModel):

    username: str

    email: EmailStr

    password: str

    full_name: str

    role: str = "TESTER"

    team: str | None = None

    core_skills: str | None = None

    proficiency: str | None = None


# ============================================================
# GET ALL ACTIVE USERS - ADMIN ONLY
# ============================================================
@router.get("/")
def get_all_users(
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of users to skip"
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of users to return"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get all active users with pagination.

    Only ADMIN users can access this endpoint.
    Used by the admin dashboard for issue assignment
    and developer matching.
    """

    users = (
        db.query(User)
        .filter(User.is_active == True)
        .order_by(User.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "team": user.team,
            "core_skills": user.core_skills,
            "proficiency": user.proficiency,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
        for user in users
    ]
# ============================================================
# CREATE USER / DEVELOPER - ADMIN ONLY
# ============================================================

@router.post("/")
def create_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new BugFlow user.

    Only ADMIN users can create users.

    Developers can have:
    - Team
    - Core Skills
    - Proficiency

    These details are used by the
    Smart Developer Matcher.
    """

    # --------------------------------------------------------
    # Validate role
    # --------------------------------------------------------

    allowed_roles = {
        "ADMIN",
        "TRIAGER",
        "DEVELOPER",
        "TESTER"
    }

    role = request.role.upper().strip()

    if role not in allowed_roles:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid role. Allowed roles: "
                "ADMIN, TRIAGER, DEVELOPER, TESTER."
            )
        )


    # --------------------------------------------------------
    # Check username
    # --------------------------------------------------------

    existing_username = (
        db.query(User)
        .filter(
            User.username == request.username.strip()
        )
        .first()
    )

    if existing_username:

        raise HTTPException(
            status_code=400,
            detail="Username already exists."
        )


    # --------------------------------------------------------
    # Check email
    # --------------------------------------------------------

    existing_email = (
        db.query(User)
        .filter(
            User.email == request.email.lower().strip()
        )
        .first()
    )

    if existing_email:

        raise HTTPException(
            status_code=400,
            detail="Email already exists."
        )


    # --------------------------------------------------------
    # Validate password
    # --------------------------------------------------------

    if len(request.password) < 6:

        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters."
        )


    # --------------------------------------------------------
    # Create user
    # --------------------------------------------------------

    new_user = User(

        username=request.username.strip(),

        email=request.email.lower().strip(),

        hashed_password=hash_password(
            request.password
        ),

        full_name=request.full_name.strip(),

        role=role,

        team=(
            request.team.strip()
            if request.team
            else None
        ),

        core_skills=(
            request.core_skills.strip()
            if request.core_skills
            else None
        ),

        proficiency=(
            request.proficiency.strip()
            if request.proficiency
            else None
        ),

        is_active=True,

        created_at=datetime.utcnow()
    )


    db.add(new_user)

    db.commit()

    db.refresh(new_user)


    # --------------------------------------------------------
    # Return created user
    # --------------------------------------------------------

    return {

        "message":
            "User created successfully.",

        "user": {

            "id":
                new_user.id,

            "username":
                new_user.username,

            "full_name":
                new_user.full_name,

            "email":
                new_user.email,

            "role":
                new_user.role,

            "team":
                new_user.team,

            "core_skills":
                new_user.core_skills,

            "proficiency":
                new_user.proficiency,

            "is_active":
                new_user.is_active,

            "created_at":
                new_user.created_at

        }

    }