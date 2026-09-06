from datetime import datetime
from enum import Enum
from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Index
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


# ============================================================
# ISSUE ENUMS
# ============================================================

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    TRIVIAL = "TRIVIAL"


class Priority(str, Enum):
    URGENT = "URGENT"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class IssueStatus(str, Enum):
    REPORTED = "REPORTED"
    TRIAGED = "TRIAGED"
    IN_PROGRESS = "IN_PROGRESS"
    CODE_REVIEW = "CODE_REVIEW"
    QA_VERIFICATION = "QA_VERIFICATION"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
class IssueType(str, Enum):
    BUG = "BUG"
    FEATURE_REQUEST = "FEATURE_REQUEST"
    ENHANCEMENT = "ENHANCEMENT"
    TECHNICAL_DEBT = "TECHNICAL_DEBT"
    SUPPORT_TICKET = "SUPPORT_TICKET"

# ============================================================
# ISSUE MODEL
# ============================================================

class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # --------------------------------------------------------
    # ASSOCIATIONS
    # --------------------------------------------------------

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.project_id"),
        nullable=False,
        index=True
    )

    reporter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("bug_categories.category_id"),
        nullable=False,
        index=True
    )

    # Sprint table is not part of Module 1 schema,
    # therefore sprint_id is kept as an optional field.
    sprint_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )

    # --------------------------------------------------------
    # CORE ISSUE INFORMATION
    # --------------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    reproduction_steps: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # CLASSIFICATION
    # --------------------------------------------------------

    issue_type: Mapped[IssueType] = mapped_column(
    SQLEnum(IssueType),
    nullable=False,
    default=IssueType.BUG,
    index=True
)
    severity: Mapped[Severity] = mapped_column(
        SQLEnum(Severity),
        nullable=False,
        default=Severity.MINOR,
        index=True
    )

    priority: Mapped[Priority] = mapped_column(
        SQLEnum(Priority),
        nullable=False,
        default=Priority.MEDIUM,
        index=True
    )

    status: Mapped[IssueStatus] = mapped_column(
        SQLEnum(IssueStatus),
        nullable=False,
        default=IssueStatus.REPORTED,
        index=True
    )

    # Developer stage can be expanded later as the
    # development workflow becomes more detailed.
    dev_stage: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    


    # --------------------------------------------------------
    # TARGET CONTEXT
    # --------------------------------------------------------

    affected_modules: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    environment_details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    estimated_effort: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    priority_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    # --------------------------------------------------------
    # TIMESTAMPS
    # --------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )
    __table_args__ = (
    Index(
        "ix_issues_project_status",
        "project_id",
        "status"
    ),
)