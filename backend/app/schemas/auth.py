from pydantic import BaseModel, EmailStr, Field


# ============================================================
# REGISTER REQUEST
# ============================================================

class RegisterRequest(BaseModel):

    username: str = Field(
        min_length=3,
        max_length=50
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )

    full_name: str = Field(
        min_length=2,
        max_length=100
    )

    role: str = "TESTER"

    team: str | None = None

    core_skills: str | None = None

    proficiency: str | None = None


# ============================================================
# LOGIN REQUEST
# ============================================================

class LoginRequest(BaseModel):

    identifier: str = Field(
        min_length=1,
        max_length=255
    )

    password: str = Field(
        min_length=1,
        max_length=128
    )


# ============================================================
# USER RESPONSE
# ============================================================

class UserResponse(BaseModel):

    id: int

    username: str

    email: EmailStr

    full_name: str

    role: str

    team: str | None

    core_skills: str | None

    proficiency: str | None

    is_active: bool

    model_config = {
        "from_attributes": True
    }


# ============================================================
# TOKEN RESPONSE
# ============================================================

class TokenResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    user: UserResponse