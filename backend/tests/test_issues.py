import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ============================================================
# LOGIN HELPER
# ============================================================

def get_token(identifier, password):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": identifier,
            "password": password
        }
    )

    assert response.status_code == 200

    return response.json()["access_token"]


# ============================================================
# TEST 1 — CREATE ISSUE WITHOUT TOKEN
# ============================================================

def test_create_issue_without_token():

    response = client.post(
        "/api/v1/issues/",
        json={
            "project_id": 1,
            "category_id": 7,
            "title": "Pytest authentication issue",
            "description": "Testing issue creation"
        }
    )

    assert response.status_code == 401


# ============================================================
# TEST 2 — CREATE ISSUE SUCCESSFULLY
# ============================================================

def test_create_issue_success():

    token = get_token(
        "pytest_user",
        "pytest_password"
    )

    response = client.post(
        "/api/v1/issues/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "project_id": 1,
            "category_id": 7,
            "title": f"Pytest authentication issue {uuid.uuid4()}",
            "description": "This issue was created by pytest.",
            "reproduction_steps": "1. Login\n2. Click authentication\n3. Observe error",
            "severity": "MINOR"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"].startswith("Pytest authentication issue ")
    assert data["project_id"] == 1
    assert data["category_id"] == 7
    assert data["status"] == "REPORTED"

    # Authentication = HIassert dataGH urgency (3)
    # MINOR severity = 2
    # Priority score = 2 × 3 = 6

    assert data["priority_score"] == 6
    assert data["priority"] == "MEDIUM"


# ============================================================
# TEST 3 — GET MY ISSUES WITH PAGINATION
# ============================================================

def test_get_my_issues_with_pagination():

    token = get_token(
        "pytest_user",
        "pytest_password"
    )

    response = client.get(
        "/api/v1/issues/my?skip=0&limit=10",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) <= 10


# ============================================================
# TEST 4 — NON-ADMIN CANNOT GET ALL ISSUES
# ============================================================

def test_non_admin_cannot_get_all_issues():

    token = get_token(
        "pytest_user",
        "pytest_password"
    )

    response = client.get(
        "/api/v1/issues/?skip=0&limit=10",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403