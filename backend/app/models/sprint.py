from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


# ============================================================
# SPRINT MODEL
# ============================================================

class Sprint(Base):
    __tablename__ = "sprints"

    # --------------------------------------------------------
    # Primary Key
    # --------------------------------------------------------

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # --------------------------------------------------------
    # Sprint Name
    # --------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # --------------------------------------------------------
    # Sprint Goal
    # --------------------------------------------------------

    goal: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # Start Date
    # --------------------------------------------------------

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    # --------------------------------------------------------
    # End Date
    # --------------------------------------------------------

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    # --------------------------------------------------------
    # Sprint Status
    # PLANNING / ACTIVE / COMPLETED
    # --------------------------------------------------------

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PLANNING"
    )

    # --------------------------------------------------------
    # Velocity
    # Number of successfully resolved issues
    # --------------------------------------------------------

    velocity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    # --------------------------------------------------------
    # Created At
    # --------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )