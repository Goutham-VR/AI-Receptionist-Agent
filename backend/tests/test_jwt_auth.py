from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.security import create_access_token, decode_access_token


client = TestClient(app)


@pytest.fixture
def mock_db():
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db

    yield db

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def active_admin():
    return SimpleNamespace(
        id=1,
        email="admin@example.com",
        is_active=True,
    )


@pytest.fixture
def valid_token():
    return create_access_token(
        admin_id=1,
        email="admin@example.com",
    )


def test_valid_token_allows_access(mock_db, active_admin, valid_token):
    mock_db.scalar.return_value = active_admin

    response = client.get(
        "/approvals/pending",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 200


def test_invalid_token_is_rejected():
    response = client.get(
        "/approvals/pending",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_missing_token_is_rejected():
    response = client.get("/approvals/pending")

    assert response.status_code == 401


def test_inactive_admin_token_is_rejected(mock_db, valid_token):
    inactive_admin = SimpleNamespace(
        id=1,
        email="admin@example.com",
        is_active=False,
    )

    mock_db.scalar.return_value = inactive_admin

    response = client.get(
        "/approvals/pending",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 401


def test_nonexistent_admin_token_is_rejected(mock_db, valid_token):
    mock_db.scalar.return_value = None

    response = client.get(
        "/approvals/pending",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 401


def test_expired_token_is_rejected():
    import os

    secret = os.getenv("JWT_SECRET_KEY")
    assert secret, "JWT_SECRET_KEY must be configured for tests"

    now = datetime.now(timezone.utc)

    expired_token = jwt.encode(
        {
            "sub": "1",
            "email": "admin@example.com",
            "role": "admin",
            "iat": int((now - timedelta(minutes=10)).timestamp()),
            "exp": int((now - timedelta(minutes=5)).timestamp()),
        },
        secret,
        algorithm="HS256",
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)


def test_token_without_admin_role_is_rejected(mock_db):
    token = create_access_token(
        admin_id=1,
        email="admin@example.com",
    )

    with patch(
        "app.auth.decode_access_token",
        return_value={
            "sub": "1",
            "email": "admin@example.com",
            "role": "user",
        },
    ):
        response = client.get(
            "/approvals/pending",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 401