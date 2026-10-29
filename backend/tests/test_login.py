from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db

client = TestClient(app)

@pytest.fixture
def mock_db():
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db

    yield db

    app.dependency_overrides.pop(get_db, None)

def test_login_with_valid_credentials(mock_db):
    admin = SimpleNamespace(
    id=1,
    email="[admin@example.com](mailto:admin@example.com)",
    hashed_password="hashed_password",
    is_active=True,
    )

    mock_db.scalar.return_value = admin

    with patch(
        "app.auth.verify_password",
        return_value=True,
    ), patch(
        "app.auth.create_access_token",
        return_value="test-access-token",
    ):
        response = client.post(
            "/auth/login",
            data={
                "username": "admin@example.com",
                "password": "CorrectPassword123!",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "test-access-token",
        "token_type": "bearer",
        "expires_in": 1800,
    }

def test_login_with_wrong_password(mock_db):
    admin = SimpleNamespace(
    id=1,
    email="[admin@example.com](mailto:admin@example.com)",
    hashed_password="hashed_password",
    is_active=True,
    )

    mock_db.scalar.return_value = admin

    with patch(
        "app.auth.verify_password",
        return_value=False,
    ):
        response = client.post(
            "/auth/login",
            data={
                "username": "admin@example.com",
                "password": "WrongPassword123!",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."

def test_login_with_unknown_email(mock_db):
    mock_db.scalar.return_value = None

    response = client.post(
        "/auth/login",
        data={
            "username": "unknown@example.com",
            "password": "AnyPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."

def test_login_with_inactive_admin(mock_db):
    admin = SimpleNamespace(
    id=1,
    email="[admin@example.com](mailto:admin@example.com)",
    hashed_password="hashed_password",
    is_active=False,
    )

    mock_db.scalar.return_value = admin

    response = client.post(
        "/auth/login",
        data={
            "username": "admin@example.com",
            "password": "CorrectPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."
