from sqlalchemy import Column, Integer, String
from app.database.database import Base


class BugCategory(Base):
    __tablename__ = "bug_categories"

    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100), nullable=False, unique=True)
    urgency = Column(String(20), nullable=False)