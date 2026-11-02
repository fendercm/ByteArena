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


def test_set_result_picks_winner_by_score() -> None:
    response = client.post("/matches/5/result", json={"score1": 8, "score2": 13})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "finished"
    assert body["winner_id"] == body["team2_id"]


def test_set_result_rejects_draw() -> None:
    response = client.post("/matches/5/result", json={"score1": 13, "score2": 13})
    assert response.status_code == 422


def test_set_result_rejects_negative_score() -> None:
    response = client.post("/matches/5/result", json={"score1": -1, "score2": 13})
    assert response.status_code == 422
