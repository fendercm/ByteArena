from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.config import settings

ACCESS_TOKEN_EXPIRE_DAYS = 7
ACCESS_TOKEN_COOKIE = "access_token"


def _jwt_secret() -> str:
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET не настроен. Добавьте секрет в .env.")
    return settings.jwt_secret


def create_access_token(user_id: int) -> str:
    """JWT для пользователя: в sub его id, срок действия 7 дней."""
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(UTC) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Проверяет подпись и срок токена. Для неверного или истёкшего токена возвращает None."""
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError:
        return None
    return payload if isinstance(payload, dict) else None
