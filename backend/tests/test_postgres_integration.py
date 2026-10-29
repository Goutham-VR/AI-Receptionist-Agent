import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta, timezone

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.models import Base, CalendarSlot, Booking, PendingApproval
from app.tools.approval_tools import approve_booking, reject_booking
from sqlalchemy.exc import IntegrityError

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_FILE)


@pytest.fixture(scope="module")
def postgres_engine():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        pytest.fail("DATABASE_URL is missing.")

    url = make_url(database_url)

    if url.get_backend_name() != "postgresql":
        pytest.fail("These tests require PostgreSQL.")

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
    )

    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")

        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db(postgres_engine):
    connection = postgres_engine.connect()
    outer_transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        join_transaction_mode="create_savepoint",
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


def create_slot_and_approval(db):
    unique_value = uuid4().hex
    now = datetime.now(timezone.utc)

    slot = CalendarSlot(
        start_time=now + timedelta(days=365, seconds=len(unique_value)),
        end_time=now + timedelta(days=365, minutes=30, seconds=len(unique_value)),
        status="available",
    )

    db.add(slot)
    db.flush()

    approval = PendingApproval(
        slot_id=slot.id,
        customer_name=f"Integration Test {unique_value}",
        customer_email=f"test-{unique_value}@example.invalid",
        status="pending",
    )

    db.add(approval)
    db.flush()

    return slot.id, approval.id


def test_postgres_connection(postgres_engine):
    assert postgres_engine.dialect.name == "postgresql"

    with postgres_engine.connect() as connection:
        result = connection.exec_driver_sql("SELECT 1").scalar_one()

    assert result == 1


def test_approve_booking_updates_postgres(db):
    slot_id, approval_id = create_slot_and_approval(db)

    result = approve_booking(
        db=db,
        approval_id=approval_id,
        reviewed_by="integration-test-admin",
    )

    assert result["success"] is True

    slot = db.get(CalendarSlot, slot_id)
    approval = db.get(PendingApproval, approval_id)

    bookings = db.scalars(
        select(Booking).where(Booking.slot_id == slot_id)
    ).all()

    assert slot.status == "booked"
    assert approval.status == "approved"
    assert approval.reviewed_by == "integration-test-admin"
    assert approval.reviewed_at is not None

    assert len(bookings) == 1
    assert bookings[0].status == "confirmed"


def test_reject_booking_does_not_create_booking(db):
    slot_id, approval_id = create_slot_and_approval(db)

    result = reject_booking(
        db=db,
        approval_id=approval_id,
        reviewed_by="integration-test-admin",
    )

    assert result["success"] is True

    slot = db.get(CalendarSlot, slot_id)
    approval = db.get(PendingApproval, approval_id)

    bookings = db.scalars(
        select(Booking).where(Booking.slot_id == slot_id)
    ).all()

    assert approval.status == "rejected"
    assert approval.reviewed_by == "integration-test-admin"
    assert approval.reviewed_at is not None

    assert slot.status == "available"
    assert len(bookings) == 0
    
def test_postgres_prevents_duplicate_bookings(db):
    slot_id, approval_id = create_slot_and_approval(db)

    first_booking = Booking(
        slot_id=slot_id,
        customer_name="First Customer",
        customer_email="first@example.com",
        status="confirmed",
    )

    db.add(first_booking)
    db.flush()

    duplicate_booking = Booking(
        slot_id=slot_id,
        customer_name="Second Customer",
        customer_email="second@example.com",
        status="confirmed",
    )

    db.add(duplicate_booking)

    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()