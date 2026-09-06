from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.rbac import require_roles
from app.database.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse


router = APIRouter(
    prefix="/api/v1/projects",
    tags=["Projects"]
)


# ============================================================
# CREATE PROJECT
# ADMIN and TRIAGER only
# ============================================================

@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("ADMIN", "TRIAGER"))
):
    """
    Create a new project.

    Allowed roles:
    - ADMIN
    - TRIAGER
    """

    # Check whether project name already exists
    existing_project = (
        db.query(Project)
        .filter(Project.project_name == project_data.project_name)
        .first()
    )

    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project with this name already exists"
        )

    new_project = Project(
        project_name=project_data.project_name,
        codebase=project_data.codebase,
        development_cycle=project_data.development_cycle
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


# ============================================================
# LIST PROJECTS
# ALL AUTHENTICATED USERS
# ============================================================

@router.get(
    "/",
    response_model=list[ProjectResponse]
)
def get_projects(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Return all projects.

    Any authenticated BugFlow user can view projects.
    """

    projects = (
        db.query(Project)
        .order_by(Project.created_at.desc())
        .all()
    )

    return projects