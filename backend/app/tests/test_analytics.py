from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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


def test_developer_workload_without_token():
    response = client.get("/api/v1/analytics/developer-workload")

    assert response.status_code == 200


def test_developer_workload_success():
    token = get_token("pytest_user", "pytest_password")

    response = client.get(
        "/api/v1/analytics/developer-workload",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "total_developers" in data
    assert "developers" in data

    assert isinstance(data["total_developers"], int)
    assert isinstance(data["developers"], list)


def test_developer_workload_structure():
    token = get_token("pytest_user", "pytest_password")

    response = client.get(
        "/api/v1/analytics/developer-workload",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    if data["developers"]:
        developer = data["developers"][0]

        assert "developer_id" in developer
        assert "developer" in developer
        assert "username" in developer
        assert "team" in developer
        assert "active_tasks" in developer
        assert "completed_fixes" in developer
        assert "average_mttr_hours" in developer
        assert "workload_status" in developer


def test_developer_workload_values():
    token = get_token("pytest_user", "pytest_password")

    response = client.get(
        "/api/v1/analytics/developer-workload",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    for developer in data["developers"]:
        assert developer["active_tasks"] >= 0
        assert developer["completed_fixes"] >= 0
        assert developer["average_mttr_hours"] >= 0

        assert developer["workload_status"] in [
            "BALANCED",
            "MEDIUM",
            "HIGH"
        ]
        