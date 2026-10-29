import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY or JWT_SECRET_KEY == "REPLACE_WITH_A_RANDOM_SECRET":
    raise RuntimeError(
        "Set a secure JWT_SECRET_KEY in your .env file."
    )

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    admin_id: int,
    email: str,
) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(admin_id),
        "email": email,
        "role": "admin",
        "iat": now,
        "exp": now + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        options={"require": ["sub", "exp"]},
    )

# Understand the important functions

# hash_password()
# Converts a plain password into a secure Argon2 password hash.

# verify_password()
# Checks a login password against the stored hash.

# create_access_token()
# Creates a signed JWT containing the administrator's ID, email, role, and expiration time.

# decode_access_token()
# Validates the token's signature and expiration before returning its payload.