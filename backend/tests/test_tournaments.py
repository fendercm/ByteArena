from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

NEW_TOURNAMENT = {
    "title": "Autumn Championship 2026",
    "starts_at": "2026-11-05T18:00:00+03:00",
    "max_teams": 8,
}


def test_list_tournaments() -> None:
    response = client.get("/tournaments")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == len(body["items"])
    assert body["items"][0]["starts_at"] == "2026-11-05T18:00:00+03:00"


def test_create_tournament() -> None:
    response = client.post("/tournaments", json=NEW_TOURNAMENT)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == NEW_TOURNAMENT["title"]
    assert body["game"] == "cs2"
    assert body["status"] == "draft"
    assert body["description"] is None


def test_create_tournament_rejects_date_without_timezone() -> None:
    response = client.post("/tournaments", json={**NEW_TOURNAMENT, "starts_at": "2026-11-05T18:00"})
    assert response.status_code == 422


def test_create_tournament_rejects_single_team() -> None:
    response = client.post("/tournaments", json={**NEW_TOURNAMENT, "max_teams": 1})
    assert response.status_code == 422


def test_get_tournament_has_teams_and_bracket() -> None:
    response = client.get("/tournaments/7")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 7
    assert len(body["teams"]) == 4
    assert all(match["tournament_id"] == 7 for match in body["matches"])

    final = next(match for match in body["matches"] if match["next_match_id"] is None)
    semifinals = [match for match in body["matches"] if match["next_match_id"] == final["id"]]
    assert len(semifinals) == 2


def test_start_tournament() -> None:
    response = client.post("/tournaments/7/start")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert body["matches"]
