from getpass import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import AdminUser
from app.security import verify_password

def main():
    email = input("Enter admin email: ").strip().lower()
    password = getpass("Enter admin password: ")

    db = SessionLocal()

    try:
        admin = db.scalar(
            select(AdminUser).where(
                AdminUser.email == email
            )
        )

        if admin is None:
            print("RESULT: Admin email not found.")
            return

        print("Admin found: YES")
        print("Admin active:", admin.is_active)

        password_matches = verify_password(
            password,
            admin.hashed_password,
        )

        print("Password matches:", password_matches)

    except Exception as error:
        print("Diagnostic error:", type(error).__name__)
        print(str(error))

    finally:
        db.close()


if __name__ == "__main__":
    main()
