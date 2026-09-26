# BugFlow – Software Issue Tracking & Resolution Platform

BugFlow is a software issue tracking and resolution platform.It is built with **FastAPI, PostgreSQL, SQLAlchemy and JWT authentication**, with a browser-based frontend.

## Project Overview



BugFlow helps development teams report, manage, assign, track, and resolve software bugs and feature requests.


## Features by Module

### Module 1 – Issue Reporting & Foundation
- Registration and login with JWT and bcrypt-hashed passwords
- Forgot / reset password with a 15-minute token
- Role-based access control: `ADMIN`, `TRIAGER`, `DEVELOPER`, `TESTER`, `STAKEHOLDER`
- User, project and bug category management
- Issue reporting (bug, feature request, enhancement, technical debt, support ticket)
- Duplicate detection: a title that matches an existing one in the same project (80%+ similarity) is rejected with `409`
- Automatic priority: severity weight × category urgency → `URGENT`, `HIGH`, `MEDIUM` or `LOW`
- Audit log of every field change (who, what, old value, new value, when)

### Module 2 – Workflow & Collaboration
- Enforced status flow: `REPORTED → TRIAGED → IN_PROGRESS → CODE_REVIEW → QA_VERIFICATION → RESOLVED → CLOSED`
- Each step is limited by role (triager, assigned developer, tester)
- Issue assignment to developers (admin only)
- Smart developer matcher: recommends the top 3 developers by skill match and current workload
- Comments and attachments (`.png`, `.jpg`, `.log`)
- Sprint planning: create, add or remove issues, start, complete, with automatic velocity
- Backlog view and activity feed
- In-app notifications

### Module 3 – Analytics & APIs
- Quality metrics: fix rate and average resolution time
- 14-day defect trends (new vs resolved)
- Plotly charts for severity distribution and workflow pipeline
- Developer workload and productivity
- CSV and PDF export of issues
- Git webhook: commit messages with `fixes #123`, `closes #123` or `resolves #123` move the issue to QA verification
- Rule-based resolution assistance from category, severity and priority
- Real-time notifications over WebSocket
- Swagger/OpenAPI docs at `/docs`

### Module 4 – Optimization & Finalization
- Composite indexes on issues: `(project_id, status)` and `(assignee_id, status)`
- Connection pooling (pool size 20, overflow 10)
- Pagination and filters on list endpoints
- Performance target of under 300 ms at 50,000+ issues
- Docker and Docker Compose deployment with health checks

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, Uvicorn |
| Auth | JWT, bcrypt |
| Database | PostgreSQL 15 |
| Frontend | HTML, CSS, JavaScript, Tailwind CSS, Plotly.js |
| Testing | pytest, FastAPI TestClient |
| Deployment | Docker, Docker Compose |

## Project Structure

```text
BugTracking_project/
├── backend/
│   ├── app/
│   │   ├── auth/         # JWT and role checks
│   │   ├── database/     # Engine and sessions
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routers/      # API endpoints
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Priority, matcher, reports, notifications
│   │   └── main.py
│   ├── tests/
│   └── pytest.ini
├── frontend/
├── .env
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Getting Started

**1. Create a `.env` file in the project root**

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bugflow_db
DB_USER=postgres
DB_PASSWORD=your_password
JWT_SECRET_KEY=your_long_random_secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**2. Run with Docker**

```bash
docker compose up --build
```

**Or run locally**

```bash
pip install -r requirements.txt
cd backend
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000` and the docs are at `http://localhost:8000/docs`. For the frontend, serve the `frontend/` folder (for example with VS Code Live Server on port 5500) and open `index.html`.

## Running Tests

```bash
cd backend
pytest
```

## User Roles

| Role | Can do |
|------|--------|
| ADMIN | Everything, including user management and issue assignment |
| TRIAGER | Create projects, triage, edit and close issues |
| DEVELOPER | Work on assigned issues and submit them for QA |
| TESTER | Verify and resolve issues in QA |
| STAKEHOLDER | Report and view issues |

