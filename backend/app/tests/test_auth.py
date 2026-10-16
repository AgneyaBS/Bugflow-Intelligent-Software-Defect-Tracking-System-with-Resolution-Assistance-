from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

def test_login_success():
    response = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "pytest_user",
            "password": "pytest_password"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data

def test_login_invalid_password():
    response = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "testuser",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401


def test_protected_endpoint_without_token():
    response = client.get("/api/v1/issues/my")

    assert response.status_code == 401