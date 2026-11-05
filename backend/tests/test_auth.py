from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_discord_login_redirects_to_authorize() -> None:
    response = client.get("/auth/discord/login", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"].startswith("https://discord.com/oauth2/authorize?")
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8080" in response.headers["location"]


def test_discord_callback_sets_access_cookie() -> None:
    response = client.get("/auth/discord/callback")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.cookies["access_token"] == "fake_jwt_token_123"
