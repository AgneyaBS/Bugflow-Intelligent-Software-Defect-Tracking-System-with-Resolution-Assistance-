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


def test_get_sprints_without_token():
    response = client.get("/api/v1/sprints/")
    assert response.status_code == 401


def test_get_sprints_with_pagination():
    token = get_token("pytest_user", "pytest_password")

    response = client.get(
        "/api/v1/sprints/?skip=0&limit=10",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) <= 10


def test_sprint_pagination_limit():
    token = get_token("pytest_user", "pytest_password")

    response = client.get(
        "/api/v1/sprints/?skip=0&limit=1",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) <= 1


def test_sprint_pagination_skip():
    token = get_token("pytest_user", "pytest_password")

    response = client.get(
        "/api/v1/sprints/?skip=1&limit=10",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) <= 10
    