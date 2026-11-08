"""Запросы к Discord. Вынесены отдельно, чтобы в тестах подменять их без сети."""

from dataclasses import dataclass

import httpx

from app.config import settings

AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/v10/oauth2/token"
ME_URL = "https://discord.com/api/v10/users/@me"
AVATAR_URL = "https://cdn.discordapp.com/avatars/{user_id}/{avatar}.png"
TIMEOUT = 10


class DiscordError(Exception):
    """Discord не ответил или ответил ошибкой."""


@dataclass
class DiscordUser:
    discord_id: str
    nickname: str
    avatar_url: str | None


def exchange_code(code: str) -> str:
    """Меняет одноразовый code из адреса возврата на токен доступа Discord."""
    try:
        response = httpx.post(
            TOKEN_URL,
            data={
                "client_id": settings.discord_client_id,
                "client_secret": settings.discord_client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.discord_redirect_uri,
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except (httpx.HTTPError, KeyError, ValueError) as error:
        raise DiscordError("Не удалось получить токен Discord") from error


def fetch_user(discord_token: str) -> DiscordUser:
    """Ник и аватар пользователя Discord по его токену."""
    try:
        response = httpx.get(
            ME_URL, headers={"Authorization": f"Bearer {discord_token}"}, timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        discord_id = str(data["id"])
        # global_name — отображаемое имя, username — логин; отображаемого может не быть
        nickname = (data.get("global_name") or data["username"])[:64]
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
        raise DiscordError("Не удалось получить профиль Discord") from error

    avatar = data.get("avatar")
    avatar_url = AVATAR_URL.format(user_id=discord_id, avatar=avatar) if avatar else None
    return DiscordUser(discord_id=discord_id, nickname=nickname, avatar_url=avatar_url)
