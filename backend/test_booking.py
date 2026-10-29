
from app.database import SessionLocal
from app.tools.booking_tools import request_booking_approval


def main():
    db = SessionLocal()

    try:
        result = request_booking_approval(
            db=db,
            slot_id=3,
            customer_name="Goutham",
            customer_email="goutham@example.com",
        )

        print(result)

    finally:
        db.close()


if __name__ == "__main__":
    main()

