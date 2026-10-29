from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.tools.booking_tools import request_booking_approval


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def available_slot():
    return SimpleNamespace(
        id=1,
        status="available",
    )


def test_booking_request_success(mock_db, available_slot):
    mock_db.scalar.side_effect = [
        available_slot,
        None,
    ]

    def set_approval_id(approval):
        approval.id = 101

    mock_db.refresh.side_effect = set_approval_id

    result = request_booking_approval(
        db=mock_db,
        slot_id=1,
        customer_name="John Smith",
        customer_email="john@example.com",
    )

    assert result["success"] is True
    assert result["approval_id"] == 101
    assert result["slot_id"] == 1
    assert result["status"] == "pending"

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


def test_booking_request_rejects_empty_name(mock_db):
    result = request_booking_approval(
        db=mock_db,
        slot_id=1,
        customer_name="   ",
        customer_email="john@example.com",
    )

    assert result["success"] is False
    assert result["message"] == (
        "Customer name and email are required."
    )

    mock_db.scalar.assert_not_called()
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


def test_booking_request_rejects_empty_email(mock_db):
    result = request_booking_approval(
        db=mock_db,
        slot_id=1,
        customer_name="John Smith",
        customer_email="   ",
    )

    assert result["success"] is False
    assert result["message"] == (
        "Customer name and email are required."
    )

    mock_db.scalar.assert_not_called()
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


def test_booking_request_rejects_missing_slot(mock_db):
    mock_db.scalar.return_value = None

    result = request_booking_approval(
        db=mock_db,
        slot_id=999,
        customer_name="John Smith",
        customer_email="john@example.com",
    )

    assert result["success"] is False
    assert result["message"] == "Appointment slot not found."

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


def test_booking_request_rejects_unavailable_slot(
    mock_db,
):
    unavailable_slot = SimpleNamespace(
        id=1,
        status="booked",
    )

    mock_db.scalar.return_value = unavailable_slot

    result = request_booking_approval(
        db=mock_db,
        slot_id=1,
        customer_name="John Smith",
        customer_email="john@example.com",
    )

    assert result["success"] is False
    assert result["message"] == (
        "This appointment slot is no longer available."
    )

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


def test_booking_request_rejects_duplicate_pending_request(
    mock_db,
    available_slot,
):
    existing_request = SimpleNamespace(
        slot_id=1,
        status="pending",
    )

    mock_db.scalar.side_effect = [
        available_slot,
        existing_request,
    ]

    result = request_booking_approval(
        db=mock_db,
        slot_id=1,
        customer_name="John Smith",
        customer_email="john@example.com",
    )

    assert result["success"] is False
    assert "already exists" in result["message"]

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


def test_booking_request_handles_integrity_error(
    mock_db,
    available_slot,
):
    mock_db.scalar.side_effect = [
        available_slot,
        None,
    ]

    mock_db.commit.side_effect = IntegrityError(
        "INSERT",
        {},
        Exception("Duplicate request"),
    )

    result = request_booking_approval(
        db=mock_db,
        slot_id=1,
        customer_name="John Smith",
        customer_email="john@example.com",
    )

    assert result["success"] is False
    assert "Another request was submitted" in result["message"]

    mock_db.rollback.assert_called_once()


def test_booking_request_rolls_back_unexpected_error(
    mock_db,
):
    mock_db.scalar.side_effect = RuntimeError(
        "Database failure"
    )

    with pytest.raises(
        RuntimeError,
        match="Database failure",
    ):
        request_booking_approval(
            db=mock_db,
            slot_id=1,
            customer_name="John Smith",
            customer_email="john@example.com",
        )

    mock_db.rollback.assert_called_once()