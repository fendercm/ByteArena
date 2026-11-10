import secrets
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.auth import discord
from app.auth.security import (
    ACCESS_TOKEN_COOKIE,
    ACCESS_TOKEN_EXPIRE_DAYS,
    create_access_token,
)
from app.config import settings
from app.db import DbSession
from app.models.user import User
from app.schemas.common import ErrorOut

router = APIRouter(prefix="/auth", tags=["auth"])

# случайная строка, которую Discord возвращает обратно: так мы знаем, что вход начат на нашем сайте
STATE_COOKIE = "oauth_state"
STATE_MAX_AGE = 10 * 60


def _set_cookie(response: Response, key: str, value: str, max_age: int) -> None:
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def _delete_cookie(response: Response, key: str) -> None:
    response.delete_cookie(key=key, httponly=True, secure=settings.cookie_secure, samesite="lax")


def _login_response(user: User) -> RedirectResponse:
    """После входа — на главную, с cookie входа на 7 дней."""
    response = RedirectResponse(url="/", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    _set_cookie(
        response,
        ACCESS_TOKEN_COOKIE,
        create_access_token(user.id),
        max_age=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    _delete_cookie(response, STATE_COOKIE)
    return response


@router.get(
    "/discord/login",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    responses={503: {"model": ErrorOut}},
)
def discord_login() -> RedirectResponse:
    """Отправить человека в Discord на страницу «пустить ByteArena?»."""
    # проверяем до похода в Discord, иначе человек авторизуется там и получит ошибку на возврате
    missing = [
        name
        for name, value in [
            ("DISCORD_CLIENT_ID", settings.discord_client_id),
            ("DISCORD_CLIENT_SECRET", settings.discord_client_secret),
            ("JWT_SECRET", settings.jwt_secret),
        ]
        if not value
    ]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Вход через Discord не настроен: в .env нет {', '.join(missing)}",
        )
    state = secrets.token_urlsafe(32)
    query = urlencode(
        {
            "client_id": settings.discord_client_id,
            "redirect_uri": settings.discord_redirect_uri,
            "response_type": "code",
            "scope": "identify",
            "state": state,
        }
    )
    response = RedirectResponse(url=f"{discord.AUTHORIZE_URL}?{query}")
    _set_cookie(response, STATE_COOKIE, state, max_age=STATE_MAX_AGE)
    return response


@router.get(
    "/discord/callback",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    responses={400: {"model": ErrorOut}, 502: {"model": ErrorOut}},
)
def discord_callback(
    db: DbSession,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    oauth_state: Annotated[str | None, Cookie()] = None,
) -> RedirectResponse:
    """Сюда Discord возвращает человека: создаём или обновляем игрока и ставим cookie входа."""
    if error:
        # человек нажал «Отмена» в Discord — просто возвращаем на главную
        response = RedirectResponse(url="/", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        _delete_cookie(response, STATE_COOKIE)
        return response

    # сравниваем байты: строку с не-ASCII символами compare_digest не принимает и падает
    if not (
        code
        and state
        and oauth_state
        and secrets.compare_digest(state.encode(), oauth_state.encode())
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вход устарел или начат не на нашем сайте. Нажмите «Войти» ещё раз",
        )

    try:
        profile = discord.fetch_user(discord.exchange_code(code))
    except discord.DiscordError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Discord не ответил. Попробуйте войти ещё раз",
        ) from None

    user = db.scalar(select(User).where(User.discord_id == profile.discord_id))
    if user is None:
        user = User(discord_id=profile.discord_id)
        db.add(user)
    # ник и аватар обновляются при каждом входе: человек мог сменить их в Discord
    user.nickname = profile.nickname
    user.avatar_url = profile.avatar_url
    db.commit()
    return _login_response(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> Response:
    """Выйти: удалить cookie входа."""
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    _delete_cookie(response, ACCESS_TOKEN_COOKIE)
    return response


@router.post(
    "/debug-login/{user_id}",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    responses={404: {"model": ErrorOut}},
)
def debug_login(user_id: int, db: DbSession) -> RedirectResponse:
    """Только для разработки (DEBUG_AUTH_ENABLED=true): войти игроком без Discord."""
    user = db.get(User, user_id) if settings.debug_auth_enabled else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено")
    return _login_response(user)
