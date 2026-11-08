from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.db import get_db
from app.models.user import User


def get_current_user(
    db: Session = Depends(get_db),
    access_token: str | None = Cookie(default=None),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Вы не авторизованы",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not access_token:
        raise unauthorized

    payload = decode_access_token(access_token)
    subject = payload.get("sub") if payload else None
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise unauthorized from None

    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user