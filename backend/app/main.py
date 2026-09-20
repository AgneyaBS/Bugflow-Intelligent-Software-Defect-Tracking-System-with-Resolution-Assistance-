from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.resolution_router import router as resolution_router
from app.database.database import Base, engine
from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.issues import router as issues_router
from app.routers.categories import router as categories_router
from app.routers.users import router as users_router
# Import models so SQLAlchemy knows about all tables
from app.models.user import User
from app.routers import collaboration
from app.models.project import Project
from app.models.bug_category import BugCategory
from app.models.issue import Issue
from app.models.audit_log import AuditLog
from app.models.comment import Comment
from app.models.attachment import Attachment
from app.routers.sprints import router as sprints_router
from app.routers.analytics import router as analytics_router
from app.routers.webhooks import router as webhooks_router
from app.routers.password_router import router as password_router
from app.routers.exports import router as exports_router
from app.routers.notifications import router as notifications_router
from app.routers.profile_router import router as profile_router


app = FastAPI(
    title="BugFlow - Software Issue Tracking & Resolution Platform",
    description="Module 1: Issue Reporting & Foundation Management",
    version="1.0.0"
)

# ============================================================
# CORS CONFIGURATION
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "null",
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables if they do not already exist
Base.metadata.create_all(bind=engine)


# Register API routes
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(issues_router)
app.include_router(categories_router)
app.include_router(users_router)
app.include_router(collaboration.router)
app.include_router(sprints_router)
app.include_router(analytics_router)
app.include_router(webhooks_router)
app.include_router(resolution_router)
app.include_router(password_router)
app.include_router(exports_router)

app.include_router(notifications_router)
app.include_router(profile_router)


@app.get("/")
def root():
    return {
        "message": "BugFlow API is running",
        "version": "1.0.0"
    }
@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }