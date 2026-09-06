from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class BugCategory(Base):
    __tablename__ = "bug_categories"

    category_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    category_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    urgency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MEDIUM"
    )