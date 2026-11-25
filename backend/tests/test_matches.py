from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_match_has_team_names() -> None:
    response = client.get("/matches/5")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 5
    assert body["team1"]["name"]
    assert body["team2"]["name"]
