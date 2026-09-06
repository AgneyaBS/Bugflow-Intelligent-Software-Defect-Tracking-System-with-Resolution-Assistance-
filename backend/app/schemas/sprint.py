from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# CREATE SPRINT REQUEST
# ============================================================

class SprintCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

    goal: str | None = None

    start_date: date

    end_date: date

    status: str = Field(
        default="PLANNING",
        pattern="^(PLANNING|ACTIVE|COMPLETED)$"
    )


# ============================================================
# SPRINT RESPONSE
# ============================================================

class SprintResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    name: str

    goal: str | None

    start_date: date

    end_date: date

    status: str

    velocity: int

    created_at: datetime