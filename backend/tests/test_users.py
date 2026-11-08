from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_me_requires_login() -> None:
    # сам вход и /me после него проверяются в test_auth.py
    response = client.get("/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Сначала войдите через Discord"}


def test_get_user_profile() -> None:
    response = client.get("/users/7")
    assert response.status_code == 200
    assert response.json()["id"] == 7
    assert response.json()["nickname"] == "Player123"
    assert "avatar_url" in response.json()
