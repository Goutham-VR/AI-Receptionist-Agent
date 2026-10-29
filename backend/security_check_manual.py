from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def main():
    password = "Example-Password-123!"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password)
    assert not verify_password("Wrong-Password", hashed_password)

    token = create_access_token(
        admin_id=1,
        email="admin@example.com",
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "1"
    assert payload["email"] == "admin@example.com"
    assert payload["role"] == "admin"

    print("Password hashing: PASS")
    print("Correct password verification: PASS")
    print("Incorrect password verification: PASS")
    print("JWT creation: PASS")
    print("JWT validation: PASS")


if __name__ == "__main__":
    main()