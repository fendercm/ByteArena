from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.config import settings

ACCESS_TOKEN_EXPIRE_DAYS = 7


def _jwt_secret() -> str:
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET не настроен. Добавьте секрет в .env.")
    return settings.jwt_secret


def create_access_token(data: dict[str, Any]) -> str:
    """Создает JWT-токен доступа с семидневным сроком действия."""
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode(payload, _jwt_secret(), algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Проверяет и декодирует токен; для невалидного или истекшего токена возвращает None."""
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError:
        return None
    return payload if isinstance(payload, dict) else None