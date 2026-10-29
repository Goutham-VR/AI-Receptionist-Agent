import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import AdminUser
from app.security import hash_password


def main():
    username = input("Enter admin username: ").strip()
    email = input("Enter admin email: ").strip().lower()
    password = getpass.getpass("Enter admin password: ")
    confirm_password = getpass.getpass("Confirm admin password: ")

    if not username or not email or not password:
        print("Username, email, and password are required.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    if len(password) < 8:
        print("Use a password with at least 8 characters.")
        return

    db = SessionLocal()

    try:
        existing_admin = db.scalar(
            select(AdminUser).where(
                (AdminUser.username == username)
                | (AdminUser.email == email)
            )
        )

        if existing_admin:
            print("An administrator with this username or email already exists.")
            return

        admin = AdminUser(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
        )

        db.add(admin)
        db.commit()

        print("Administrator created successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()