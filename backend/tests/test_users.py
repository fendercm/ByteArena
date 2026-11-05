from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_current_user() -> None:
    response = client.get("/me")
    assert response.status_code == 200
    assert response.json()["nickname"] == "Fedor"
    assert "avatar_url" in response.json()


def test_get_user_profile() -> None:
    response = client.get("/users/7")
    assert response.status_code == 200
    assert response.json()["id"] == 7
    assert response.json()["nickname"] == "Player123"
    assert "avatar_url" in response.json()
