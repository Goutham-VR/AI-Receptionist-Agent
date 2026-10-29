
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import CalendarSlot, Booking, PendingApproval

def get_pending_approvals(db: Session) -> dict:
    approvals = db.scalars(
        select(PendingApproval)
        .where(PendingApproval.status == "pending")
        .order_by(PendingApproval.created_at)
    ).all()

    return {
        "success": True,
        "count": len(approvals),
        "approvals": [
            {
                "approval_id": approval.id,
                "slot_id": approval.slot_id,
                "customer_name": approval.customer_name,
                "customer_email": approval.customer_email,
                "status": approval.status,
                "created_at": (
                    approval.created_at.isoformat()
                    if approval.created_at
                    else None
                ),
            }
            for approval in approvals
        ],
    }


def approve_booking(
    db: Session,
    approval_id: int,
    reviewed_by: str,
) -> dict:
    try:
        # Lock the approval row so concurrent approvals cannot process it twice.
        approval = db.scalar(
            select(PendingApproval)
            .where(PendingApproval.id == approval_id)
            .with_for_update()
        )

        if approval is None:
            db.rollback()
            return {
                "success": False,
                "message": "Approval request not found.",
            }

        if approval.status != "pending":
            db.rollback()
            return {
                "success": False,
                "message": f"This request is already {approval.status}.",
            }

        # Lock the appointment slot before confirming the booking.
        slot = db.scalar(
            select(CalendarSlot)
            .where(CalendarSlot.id == approval.slot_id)
            .with_for_update()
        )

        if slot is None:
            db.rollback()
            return {
                "success": False,
                "message": "Appointment slot not found.",
            }

        if slot.status != "available":
            db.rollback()
            return {
                "success": False,
                "message": "This appointment slot is no longer available.",
            }

        # Create the confirmed booking.
        booking = Booking(
            slot_id=slot.id,
            customer_name=approval.customer_name,
            customer_email=approval.customer_email,
            status="confirmed",
        )

        db.add(booking)

        # Mark the slot as booked.
        slot.status = "booked"

        # Record who approved the request and when.
        approval.status = "approved"
        approval.reviewed_by = reviewed_by
        approval.reviewed_at = datetime.now(timezone.utc)

        # Commit all changes together.
        db.commit()
        db.refresh(booking)

        return {
            "success": True,
            "message": "Booking approved and confirmed successfully.",
            "booking_id": booking.id,
            "approval_id": approval.id,
            "slot_id": booking.slot_id,
            "customer_name": booking.customer_name,
            "customer_email": booking.customer_email,
            "status": booking.status,
        }

    except Exception:
        db.rollback()
        raise

def reject_booking(
    db: Session,
    approval_id: int,
    reviewed_by: str,
) -> dict:
    try:
        approval = db.scalar(
            select(PendingApproval)
            .where(PendingApproval.id == approval_id)
            .with_for_update()
        )

        if approval is None:
            return {
                "success": False,
                "message": "Approval request not found.",
            }

        if approval.status != "pending":
            return {
                "success": False,
                "message": f"This request has already been {approval.status}.",
            }

        approval.status = "rejected"
        approval.reviewed_by = reviewed_by
        approval.reviewed_at = datetime.now(timezone.utc)

        db.commit()

        return {
            "success": True,
            "message": "Booking request rejected successfully.",
            "approval_id": approval.id,
            "slot_id": approval.slot_id,
            "customer_name": approval.customer_name,
            "customer_email": approval.customer_email,
            "status": approval.status,
        }

    except Exception:
        db.rollback()
        raise