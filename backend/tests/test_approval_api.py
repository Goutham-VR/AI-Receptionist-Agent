from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.auth import get_current_admin
from app.database import get_db
from app.models import AdminUser

client = TestClient(app)


def mock_admin():
    from types import SimpleNamespace

    return SimpleNamespace(
        id=1,
        email="admin@example.com",
        is_active=True,
    )


def override_get_current_admin():
    return mock_admin()


def override_get_db():
    yield MagicMock()


def setup_authenticated_client():
    app.dependency_overrides[get_current_admin] = (
        override_get_current_admin
    )
    app.dependency_overrides[get_db] = override_get_db


def teardown_authenticated_client():
    app.dependency_overrides.clear()


def test_approve_missing_request_returns_404(monkeypatch):
    from app import main

    setup_authenticated_client()

    monkeypatch.setattr(
        main,
        "approve_booking",
        lambda **kwargs: {
            "success": False,
            "message": "Approval request not found.",
        },
    )

    try:
        response = client.post("/approvals/999999/approve")
        assert response.status_code == 404
    finally:
        teardown_authenticated_client()


def test_approve_already_reviewed_returns_409(monkeypatch):
    from app import main

    setup_authenticated_client()

    monkeypatch.setattr(
        main,
        "approve_booking",
        lambda **kwargs: {
            "success": False,
            "message": "This request is already approved.",
        },
    )

    try:
        response = client.post("/approvals/1/approve")
        assert response.status_code == 409
    finally:
        teardown_authenticated_client()


def test_reject_missing_request_returns_404(monkeypatch):
    from app import main

    setup_authenticated_client()

    monkeypatch.setattr(
        main,
        "reject_booking",
        lambda **kwargs: {
            "success": False,
            "message": "Approval request not found.",
        },
    )

    try:
        response = client.post("/approvals/999999/reject")
        assert response.status_code == 404
    finally:
        teardown_authenticated_client()


def test_reject_already_reviewed_returns_409(monkeypatch):
    from app import main

    setup_authenticated_client()

    monkeypatch.setattr(
        main,
        "reject_booking",
        lambda **kwargs: {
            "success": False,
            "message": "This request has already been approved.",
        },
    )

    try:
        response = client.post("/approvals/1/reject")
        assert response.status_code == 409
    finally:
        teardown_authenticated_client()

def test_approve_booking_success(monkeypatch):
    from app import main

    setup_authenticated_client()

    def mock_approve_booking(**kwargs):
        assert kwargs["approval_id"] == 1
        assert kwargs["reviewed_by"] == "admin@example.com"

        return {
            "success": True,
            "message": "Booking approved and confirmed successfully.",
            "booking_id": 100,
            "approval_id": 1,
            "slot_id": 10,
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "status": "confirmed",
        }

    monkeypatch.setattr(
        main,
        "approve_booking",
        mock_approve_booking,
    )

    try:
        response = client.post("/approvals/1/approve")

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["booking_id"] == 100
        assert response.json()["status"] == "confirmed"

    finally:
        teardown_authenticated_client()


def test_reject_booking_success(monkeypatch):
    from app import main

    setup_authenticated_client()

    def mock_reject_booking(**kwargs):
        assert kwargs["approval_id"] == 1
        assert kwargs["reviewed_by"] == "admin@example.com"

        return {
            "success": True,
            "message": "Booking request rejected successfully.",
            "approval_id": 1,
            "slot_id": 10,
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "status": "rejected",
        }

    monkeypatch.setattr(
        main,
        "reject_booking",
        mock_reject_booking,
    )

    try:
        response = client.post("/approvals/1/reject")

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["approval_id"] == 1
        assert response.json()["status"] == "rejected"

    finally:
        teardown_authenticated_client()