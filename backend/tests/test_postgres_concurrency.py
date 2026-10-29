import os
from pathlib import Path
from threading import Thread, Barrier
from uuid import uuid4
from datetime import datetime, timedelta, timezone

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.models import CalendarSlot, Booking, PendingApproval
from app.tools.approval_tools import approve_booking


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_FILE)


@pytest.fixture(scope="module")
def postgres_session_factory():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        pytest.fail("DATABASE_URL is missing.")

    url = make_url(database_url)

    if url.get_backend_name() != "postgresql":
        pytest.fail("This test requires PostgreSQL.")

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
    )

    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")

        yield factory

    finally:
        engine.dispose()


def test_concurrent_approvals_for_same_slot(
    postgres_session_factory,
):
    factory = postgres_session_factory
    unique_value = uuid4().hex
    now = datetime.now(timezone.utc)

    slot_id = None
    approval_id = None

    # Create one slot and one pending approval.
    with factory.begin() as db:
        slot = CalendarSlot(
            start_time=now + timedelta(days=400),
            end_time=now + timedelta(days=400, minutes=30),
            status="available",
        )

        db.add(slot)
        db.flush()

        slot_id = slot.id

        approval = PendingApproval(
            slot_id=slot_id,
            customer_name=f"Concurrency Test {unique_value}",
            customer_email=f"test-{unique_value}@example.invalid",
            status="pending",
        )

        db.add(approval)
        db.flush()

        approval_id = approval.id

    barrier = Barrier(2)
    results = []
    errors = []

    def approve():
        try:
            with factory() as db:
                barrier.wait(timeout=10)

                result = approve_booking(
                    db=db,
                    approval_id=approval_id,
                    reviewed_by=f"admin-{uuid4().hex[:8]}",
                )

                results.append(result)

        except Exception as exc:
            errors.append(exc)

    threads = [
        Thread(target=approve),
        Thread(target=approve),
    ]

    try:
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=30)

        assert all(not thread.is_alive() for thread in threads), (
            "A concurrency-test thread did not finish."
        )

        assert not errors, f"Unexpected errors: {errors}"
        assert len(results) == 2

        successful = [
            result for result in results
            if result["success"]
        ]

        unsuccessful = [
            result for result in results
            if not result["success"]
        ]

        assert len(successful) == 1, results
        assert len(unsuccessful) == 1, results

        # Verify the final database state.
        with factory() as db:
            slot = db.get(CalendarSlot, slot_id)
            approval = db.get(PendingApproval, approval_id)

            bookings = db.query(Booking).filter(
                Booking.slot_id == slot_id
            ).all()

            assert slot.status == "booked"
            assert approval.status == "approved"
            assert len(bookings) == 1

    finally:
        # Delete only records created by this test.
        with factory.begin() as db:
            db.query(Booking).filter(
                Booking.slot_id == slot_id
            ).delete(synchronize_session=False)

            db.query(PendingApproval).filter(
                PendingApproval.id == approval_id
            ).delete(synchronize_session=False)

            db.query(CalendarSlot).filter(
                CalendarSlot.id == slot_id
            ).delete(synchronize_session=False)

