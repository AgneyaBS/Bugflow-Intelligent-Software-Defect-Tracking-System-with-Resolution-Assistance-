from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    project_name: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    codebase: str | None = Field(
        default=None,
        max_length=255
    )

    development_cycle: str | None = Field(
        default=None,
        max_length=100
    )


class ProjectResponse(BaseModel):
    project_id: int
    project_name: str
    codebase: str | None
    development_cycle: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )