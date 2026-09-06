from app.database.database import Base, engine

# Import all models so SQLAlchemy registers their tables
from app.models import (
    User,
    Project,
    BugCategory,
    Issue,
    AuditLog,
)


print("Creating BugFlow database tables...")

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")