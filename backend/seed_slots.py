from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import CalendarSlot


def seed_slots():
    db: Session = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        sample_slots = [
            CalendarSlot(
                start_time=now + timedelta(days=1, hours=1),
                end_time=now + timedelta(days=1, hours=1, minutes=30),
                status="available",
            ),
            CalendarSlot(
                start_time=now + timedelta(days=1, hours=2),
                end_time=now + timedelta(days=1, hours=2, minutes=30),
                status="available",
            ),
            CalendarSlot(
                start_time=now + timedelta(days=2, hours=3),
                end_time=now + timedelta(days=2, hours=3, minutes=30),
                status="available",
            ),
        ]

        for slot in sample_slots:
            existing_slot = db.query(CalendarSlot).filter_by(
                start_time=slot.start_time
            ).first()

            if existing_slot is None:
                db.add(slot)

        db.commit()

        print("Sample appointment slots inserted successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_slots()