from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import CalendarSlot, Booking, PendingApproval
from app.tools.approval_tools import approve_booking, reject_booking


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(
        bind=engine,
        tables=[
            CalendarSlot.__table__,
            Booking.__table__,
            PendingApproval.__table__,
        ],
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(
            bind=engine,
            tables=[
                PendingApproval.__table__,
                Booking.__table__,
                CalendarSlot.__table__,
            ],
        )
        engine.dispose()


def create_slot_and_approval(db):
    now = datetime.now(timezone.utc)

    slot = CalendarSlot(
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, minutes=30),
        status="available",
    )

    db.add(slot)
    db.flush()

    approval = PendingApproval(
        slot_id=slot.id,
        customer_name="John Doe",
        customer_email="john@example.com",
        status="pending",
    )

    db.add(approval)
    db.commit()

    return slot.id, approval.id


def test_approve_booking_updates_database(db):
    slot_id, approval_id = create_slot_and_approval(db)

    result = approve_booking(
        db=db,
        approval_id=approval_id,
        reviewed_by="admin@example.com",
    )

    assert result["success"] is True

    slot = db.get(CalendarSlot, slot_id)
    approval = db.get(PendingApproval, approval_id)

    bookings = db.scalars(
        select(Booking).where(Booking.slot_id == slot_id)
    ).all()

    assert slot.status == "booked"
    assert approval.status == "approved"
    assert approval.reviewed_by == "admin@example.com"
    assert approval.reviewed_at is not None

    assert len(bookings) == 1
    assert bookings[0].customer_email == "john@example.com"
    assert bookings[0].status == "confirmed"


def test_reject_booking_updates_database_without_booking(db):
    slot_id, approval_id = create_slot_and_approval(db)

    result = reject_booking(
        db=db,
        approval_id=approval_id,
        reviewed_by="admin@example.com",
    )

    assert result["success"] is True

    approval = db.get(PendingApproval, approval_id)
    slot = db.get(CalendarSlot, slot_id)

    bookings = db.scalars(
        select(Booking).where(Booking.slot_id == slot_id)
    ).all()

    assert approval.status == "rejected"
    assert approval.reviewed_by == "admin@example.com"
    assert approval.reviewed_at is not None

    assert slot.status == "available"
    assert len(bookings) == 0