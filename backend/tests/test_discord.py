import httpx
import pytest

from app.auth import discord


def answer(method: str, url: str, status: int, json: dict) -> httpx.Response:
    return httpx.Response(status, json=json, request=httpx.Request(method, url))


def test_fetch_user_uses_display_name_and_builds_avatar(monkeypatch: pytest.MonkeyPatch) -> None:
    profile = {"id": "42", "username": "wolf", "global_name": "Night Wolf", "avatar": "abc"}
    monkeypatch.setattr(discord.httpx, "get", lambda url, **kw: answer("GET", url, 200, profile))
    user = discord.fetch_user("token")
    assert user == discord.DiscordUser(
        "42", "Night Wolf", "https://cdn.discordapp.com/avatars/42/abc.png"
    )


def test_fetch_user_without_display_name_or_avatar(monkeypatch: pytest.MonkeyPatch) -> None:
    profile = {"id": "42", "username": "wolf", "global_name": None, "avatar": None}
    monkeypatch.setattr(discord.httpx, "get", lambda url, **kw: answer("GET", url, 200, profile))
    assert discord.fetch_user("token") == discord.DiscordUser("42", "wolf", None)


def test_exchange_code_returns_discord_token(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = {}

    def post(url: str, data: dict, **kw) -> httpx.Response:
        sent.update(data)
        return answer("POST", url, 200, {"access_token": "discord-token"})

    monkeypatch.setattr(discord.httpx, "post", post)
    assert discord.exchange_code("abc") == "discord-token"
    assert sent["grant_type"] == "authorization_code"
    assert sent["code"] == "abc"


def test_discord_error_answer_becomes_discord_error(monkeypatch: pytest.MonkeyPatch) -> None:
    error = {"error": "invalid_grant"}
    monkeypatch.setattr(discord.httpx, "post", lambda url, **kw: answer("POST", url, 400, error))
    with pytest.raises(discord.DiscordError):
        discord.exchange_code("expired")
