from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import CalendarSlot, PendingApproval


def request_booking_approval(
    db: Session,
    slot_id: int,
    customer_name: str,
    customer_email: str,
) -> dict:
    customer_name = customer_name.strip()
    customer_email = customer_email.strip()

    if not customer_name or not customer_email:
        return {
            "success": False,
            "message": "Customer name and email are required.",
        }

    try:
        # Lock the slot to serialize requests for the same appointment.
        slot = db.scalar(
            select(CalendarSlot)
            .where(CalendarSlot.id == slot_id)
            .with_for_update()
        )

        if slot is None:
            return {
                "success": False,
                "message": "Appointment slot not found.",
            }

        if slot.status != "available":
            return {
                "success": False,
                "message": "This appointment slot is no longer available.",
            }

        # Check for an existing pending request.
        existing_request = db.scalar(
            select(PendingApproval).where(
                PendingApproval.slot_id == slot_id,
                PendingApproval.status == "pending",
            )
        )

        if existing_request is not None:
            return {
                "success": False,
                "message": (
                    "A pending approval request already exists "
                    "for this appointment slot."
                ),
            }

        approval = PendingApproval(
            slot_id=slot_id,
            customer_name=customer_name,
            customer_email=customer_email,
            status="pending",
        )

        db.add(approval)
        db.commit()
        db.refresh(approval)

        return {
            "success": True,
            "message": "Booking request submitted for human approval.",
            "approval_id": approval.id,
            "slot_id": approval.slot_id,
            "status": approval.status,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "message": (
                "Another request was submitted for this slot. "
                "Please check availability again."
            ),
        }

    except Exception:
        db.rollback()
        raise

