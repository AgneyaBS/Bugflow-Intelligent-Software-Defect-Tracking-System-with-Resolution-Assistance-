from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.bug_category import BugCategory
from app.schemas.category import CategoryResponse


router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"]
)


@router.get("/", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    categories = (
        db.query(BugCategory)
        .order_by(BugCategory.category_id)
        .all()
    )

    return categories