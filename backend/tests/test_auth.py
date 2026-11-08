from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import discord
from app.config import settings
from app.models.user import User

PROFILE = discord.DiscordUser(
    discord_id="123456789012345678901",
    nickname="Night Wolf",
    avatar_url="https://cdn.discordapp.com/avatars/123456789012345678901/abc.png",
)


@pytest.fixture
def fake_discord(monkeypatch: pytest.MonkeyPatch) -> dict[str, discord.DiscordUser]:
    """Подменяет запросы к Discord: тесты не ходят в сеть. Профиль можно менять через ["user"]."""
    current = {"user": PROFILE}
    monkeypatch.setattr(discord, "exchange_code", lambda code: f"discord-token-for-{code}")
    monkeypatch.setattr(discord, "fetch_user", lambda token: current["user"])
    return current


def login(client: TestClient) -> str:
    """Начать вход и вернуть state, который Discord потом пришлёт обратно."""
    response = client.get("/auth/discord/login")
    return parse_qs(urlparse(response.headers["location"]).query)["state"][0]


def test_login_redirects_to_discord_with_settings_and_state(client: TestClient) -> None:
    response = client.get("/auth/discord/login")
    assert response.status_code == 307
    location = urlparse(response.headers["location"])
    query = parse_qs(location.query)
    assert f"{location.scheme}://{location.netloc}{location.path}" == discord.AUTHORIZE_URL
    assert query["client_id"] == ["test-client"]
    assert query["redirect_uri"] == [settings.discord_redirect_uri]
    assert query["state"] == [client.cookies["oauth_state"]]


@pytest.mark.parametrize("field", ["discord_client_id", "discord_client_secret", "jwt_secret"])
def test_login_without_settings_is_503_before_discord(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    monkeypatch.setattr(settings, field, "")
    response = client.get("/auth/discord/login")
    assert response.status_code == 503
    assert field.upper() in response.json()["detail"]


def test_callback_creates_user_and_logs_in(client: TestClient, db: Session, fake_discord) -> None:
    state = login(client)
    response = client.get("/auth/discord/callback", params={"code": "abc", "state": state})
    assert response.status_code == 307
    assert response.headers["location"] == "/"
    assert "access_token" in client.cookies

    me = client.get("/me")
    assert me.status_code == 200
    assert me.json()["nickname"] == "Night Wolf"
    assert me.json()["avatar_url"] == PROFILE.avatar_url
    assert db.scalar(select(User.discord_id)) == PROFILE.discord_id


def test_second_login_updates_profile_without_duplicate(
    client: TestClient, db: Session, fake_discord
) -> None:
    client.get("/auth/discord/callback", params={"code": "a", "state": login(client)})
    fake_discord["user"] = discord.DiscordUser(PROFILE.discord_id, "New Nick", None)
    client.get("/auth/discord/callback", params={"code": "b", "state": login(client)})

    assert db.scalar(select(func.count()).select_from(User)) == 1
    assert client.get("/me").json() == {
        "id": 1,
        "nickname": "New Nick",
        "avatar_url": None,
    }


def test_callback_with_wrong_state_is_rejected(client: TestClient, fake_discord) -> None:
    login(client)
    response = client.get("/auth/discord/callback", params={"code": "abc", "state": "чужой"})
    assert response.status_code == 400
    assert "access_token" not in client.cookies


def test_callback_without_login_start_is_rejected(client: TestClient, fake_discord) -> None:
    response = client.get("/auth/discord/callback", params={"code": "abc", "state": "x"})
    assert response.status_code == 400


def test_cancel_in_discord_returns_home_without_login(client: TestClient) -> None:
    login(client)
    response = client.get("/auth/discord/callback", params={"error": "access_denied"})
    assert response.status_code == 307
    assert response.headers["location"] == "/"
    assert "access_token" not in client.cookies


def test_discord_failure_is_502(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(code: str) -> str:
        raise discord.DiscordError("Discord недоступен")

    monkeypatch.setattr(discord, "exchange_code", broken)
    response = client.get("/auth/discord/callback", params={"code": "abc", "state": login(client)})
    assert response.status_code == 502


def test_me_without_login_or_with_fake_token_is_401(client: TestClient) -> None:
    assert client.get("/me").status_code == 401
    client.cookies.set("access_token", "fake_jwt_token_123")
    assert client.get("/me").status_code == 401


def test_logout_forgets_user(client: TestClient, fake_discord) -> None:
    client.get("/auth/discord/callback", params={"code": "abc", "state": login(client)})
    assert client.get("/me").status_code == 200

    assert client.post("/auth/logout").status_code == 204
    assert client.get("/me").status_code == 401


def test_debug_login_is_hidden_unless_enabled(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    db.add(User(discord_id="1", nickname="Tester"))
    db.commit()
    assert client.post("/auth/debug-login/1").status_code == 404

    monkeypatch.setattr(settings, "debug_auth_enabled", True)
    assert client.post("/auth/debug-login/1").status_code == 307
    assert client.get("/me").json()["nickname"] == "Tester"
