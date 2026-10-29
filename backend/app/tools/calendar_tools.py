from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CalendarSlot


def check_slots(
    db: Session,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict:
    """
    Find available appointment slots in the requested time range.
    """

    query = select(CalendarSlot).where(
        CalendarSlot.status == "available"
    )

    if start_time is not None:
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        query = query.where(
            CalendarSlot.start_time >= start_time
        )

    if end_time is not None:
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        query = query.where(
            CalendarSlot.start_time < end_time
        )

    query = query.order_by(CalendarSlot.start_time).limit(20)

    slots = db.scalars(query).all()

    return {
        "success": True,
        "count": len(slots),
        "slots": [
            {
                "id": slot.id,
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "status": slot.status,
            }
            for slot in slots
        ],
    }
