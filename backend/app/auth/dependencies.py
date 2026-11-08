from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status

from app.auth.security import decode_access_token
from app.db import DbSession
from app.models.user import User


def get_current_user(
    db: DbSession,
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    """Проверка «кто вошёл»: пользователь из cookie access_token, иначе 401."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Сначала войдите через Discord"
    )
    payload = decode_access_token(access_token) if access_token else None
    try:
        user_id = int(payload["sub"]) if payload else None
    except (KeyError, TypeError, ValueError):
        user_id = None
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise unauthorized
    return user


# В роутах, которым нужен вошедший пользователь: `user: CurrentUser`
CurrentUser = Annotated[User, Depends(get_current_user)]
