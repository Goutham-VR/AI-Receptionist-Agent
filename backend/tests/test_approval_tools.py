from types import SimpleNamespace
from unittest.mock import MagicMock

from app.models import Booking
from app.tools.approval_tools import (
    approve_booking,
    reject_booking,
)


def create_mock_approval(
    approval_id=1,
    slot_id=10,
    status="pending",
):
    return SimpleNamespace(
        id=approval_id,
        slot_id=slot_id,
        customer_name="John Doe",
        customer_email="john@example.com",
        status=status,
        reviewed_by=None,
        reviewed_at=None,
    )


def create_mock_slot(
    slot_id=10,
    status="available",
):
    return SimpleNamespace(
        id=slot_id,
        status=status,
    )


def test_approve_booking_success():
    db = MagicMock()

    approval = create_mock_approval()
    slot = create_mock_slot()

    db.scalar.side_effect = [approval, slot]

    result = approve_booking(
        db=db,
        approval_id=1,
        reviewed_by="admin@example.com",
    )

    assert result["success"] is True
    assert result["message"] == (
        "Booking approved and confirmed successfully."
    )
    assert result["approval_id"] == 1
    assert result["slot_id"] == 10
    assert result["status"] == "confirmed"

    assert approval.status == "approved"
    assert approval.reviewed_by == "admin@example.com"
    assert approval.reviewed_at is not None

    assert slot.status == "booked"

    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_approve_booking_request_not_found():
    db = MagicMock()
    db.scalar.return_value = None

    result = approve_booking(
        db=db,
        approval_id=999,
        reviewed_by="admin@example.com",
    )

    assert result["success"] is False
    assert result["message"] == "Approval request not found."

    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_approve_booking_already_reviewed():
    db = MagicMock()

    approval = create_mock_approval(status="approved")
    db.scalar.return_value = approval

    result = approve_booking(
        db=db,
        approval_id=1,
        reviewed_by="admin@example.com",
    )

    assert result["success"] is False
    assert result["message"] == "This request is already approved."

    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.rollback.assert_called_once()


def test_approve_booking_slot_not_found():
    db = MagicMock()

    approval = create_mock_approval()
    db.scalar.side_effect = [approval, None]

    result = approve_booking(
        db=db,
        approval_id=1,
        reviewed_by="admin@example.com",
    )

    assert result["success"] is False
    assert result["message"] == "Appointment slot not found."

    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.rollback.assert_called_once()


def test_approve_booking_slot_unavailable():
    db = MagicMock()

    approval = create_mock_approval()
    slot = create_mock_slot(status="booked")

    db.scalar.side_effect = [approval, slot]

    result = approve_booking(
        db=db,
        approval_id=1,
        reviewed_by="admin@example.com",
    )

    assert result["success"] is False
    assert result["message"] == (
        "This appointment slot is no longer available."
    )

    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.rollback.assert_called_once()


def test_reject_booking_success():
    db = MagicMock()

    approval = create_mock_approval()
    db.scalar.return_value = approval

    result = reject_booking(
        db=db,
        approval_id=1,
        reviewed_by="admin@example.com",
    )

    assert result["success"] is True
    assert result["message"] == (
        "Booking request rejected successfully."
    )

    assert approval.status == "rejected"
    assert approval.reviewed_by == "admin@example.com"
    assert approval.reviewed_at is not None

    db.commit.assert_called_once()
    db.add.assert_not_called()


def test_reject_booking_request_not_found():
    db = MagicMock()
    db.scalar.return_value = None

    result = reject_booking(
        db=db,
        approval_id=999,
        reviewed_by="admin@example.com",
    )

    assert result["success"] is False
    assert result["message"] == "Approval request not found."

    db.commit.assert_not_called()


def test_reject_booking_already_reviewed():
    db = MagicMock()

    approval = create_mock_approval(status="approved")
    db.scalar.return_value = approval

    result = reject_booking(
        db=db,
        approval_id=1,
        reviewed_by="admin@example.com",
    )

    assert result["success"] is False
    assert result["message"] == (
        "This request has already been approved."
    )

    db.commit.assert_not_called()