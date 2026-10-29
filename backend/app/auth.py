from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AdminUser
from app.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/login")
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    email = form_data.username.strip().lower()

    admin = db.scalar(
        select(AdminUser).where(AdminUser.email == email)
    )

    if (
        admin is None
        or not admin.is_active
        or not verify_password(
            form_data.password,
            admin.hashed_password,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        admin_id=admin.id,
        email=admin.email,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 30 * 60,
    }


def get_current_admin(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> AdminUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")

        if not subject or payload.get("role") != "admin":
            raise credentials_exception

        admin_id = int(subject)

    except (ValueError, TypeError):
        raise credentials_exception from None

    except Exception:
        raise credentials_exception from None

    admin = db.scalar(
        select(AdminUser).where(AdminUser.id == admin_id)
    )

    if admin is None or not admin.is_active:
        raise credentials_exception

    return admin