from datetime import timedelta

import pytest
from jwt import InvalidTokenError

from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    password = "TestPassword123!"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password)


def test_wrong_password_is_rejected():
    hashed_password = hash_password("CorrectPassword123!")

    assert not verify_password(
        "WrongPassword123!",
        hashed_password,
    )


def test_access_token_contains_admin_details():
    token = create_access_token(
        admin_id=123,
        email="admin@example.com",
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "123"
    assert payload["email"] == "admin@example.com"
    assert payload["role"] == "admin"


def test_invalid_token_is_rejected():
    with pytest.raises(InvalidTokenError):
        decode_access_token("this-is-not-a-valid-token")