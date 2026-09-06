from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.issue import IssueType, Severity, Priority, IssueStatus

# ============================================================
# CREATE ISSUE REQUEST
# ============================================================

class IssueCreate(BaseModel):
    """
    Schema used when creating a new issue.
    """

    project_id: int = Field(..., gt=0)

    category_id: int = Field(..., gt=0)
    
    issue_type: IssueType = IssueType.BUG

    title: str = Field(..., min_length=3, max_length=255)

    description: str = Field(..., min_length=5)

    reproduction_steps: str | None = None

    severity: Severity = Severity.MINOR

    priority: Priority = Priority.MEDIUM

    assignee_id: int | None = Field(
        default=None,
        gt=0
    )

    sprint_id: int | None = Field(
        default=None,
        gt=0
    )

    dev_stage: str | None = Field(
        default=None,
        max_length=50
    )

    affected_modules: str | None = None

    environment_details: str | None = None

    estimated_effort: float | None = Field(
        default=None,
        ge=0
    )

    priority_score: float | None = Field(
        default=None,
        ge=0
    )
    # ============================================================
# UPDATE ISSUE REQUEST
# ============================================================

class IssueUpdate(BaseModel):
    """
    Schema used when updating an existing issue.

    All fields are optional so the user can update
    only the information that needs to be changed.
    """

    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=255
    )

    description: str | None = Field(
        default=None,
        min_length=5
    )

    reproduction_steps: str | None = None

    severity: Severity | None = None

    priority: Priority | None = None

    dev_stage: str | None = Field(
        default=None,
        max_length=50
    )

    affected_modules: str | None = None

    environment_details: str | None = None

    estimated_effort: float | None = Field(
        default=None,
        ge=0
    )

    priority_score: float | None = Field(
        default=None,
        ge=0
    )
# ============================================================
# ISSUE RESPONSE
# ============================================================

class IssueResponse(BaseModel):
    """
    Schema returned by the API after creating or retrieving
    an issue.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int

    project_id: int

    reporter_id: int

    assignee_id: int | None

    category_id: int
    
    issue_type: IssueType

    sprint_id: int | None

    title: str

    description: str

    reproduction_steps: str | None

    severity: Severity

    priority: Priority

    status: IssueStatus

    dev_stage: str | None

    affected_modules: str | None

    environment_details: str | None

    estimated_effort: float | None

    priority_score: float | None

    created_at: datetime

    updated_at: datetime

    resolved_at: datetime | None
# ============================================================
# UPDATE ISSUE STATUS
# ============================================================

class IssueStatusUpdate(BaseModel):
    """
    Schema used to update the status of an issue.
    """

    status: IssueStatus
    # ============================================================
# ASSIGN ISSUE
# ============================================================

class IssueAssignment(BaseModel):
    """
    Schema used to assign an issue to a user.
    """

    assignee_id: int = Field(..., gt=0)