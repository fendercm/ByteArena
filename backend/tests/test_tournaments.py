from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.team import Team
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
from app.models.user import User


def in_days(days: int) -> str:
    # дата считается от сегодняшнего дня, иначе тест сломается, когда она окажется в прошлом
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


NEW_TOURNAMENT = {"title": "Autumn Championship 2026", "starts_at": in_days(7), "max_teams": 8}


def add_tournament(db: Session, organizer: User, **fields) -> Tournament:
    tournament = Tournament(
        **{
            "title": "Cup",
            "starts_at": datetime.now(UTC) + timedelta(days=3),
            "max_teams": 4,
            "status": "registration",
            **fields,
        },
        organizer_id=organizer.id,
    )
    db.add(tournament)
    db.commit()
    return tournament


# --- создание ---


def test_create_requires_login(client: TestClient) -> None:
    response = client.post("/tournaments", json=NEW_TOURNAMENT)
    assert response.status_code == 401


def test_create_saves_tournament_with_organizer(logged_in: TestClient, user: User) -> None:
    response = logged_in.post("/tournaments", json=NEW_TOURNAMENT)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == NEW_TOURNAMENT["title"]
    assert body["organizer_id"] == user.id
    assert body["status"] == "registration"
    assert body["game"] == "cs2"
    assert body["teams_count"] == 0
    assert body["description"] is None
    assert body["created_at"]

    # сохранён по-настоящему: виден в списке и открывается по номеру
    assert logged_in.get("/tournaments").json()["total"] == 1
    opened = logged_in.get(f"/tournaments/{body['id']}").json()
    assert opened["title"] == NEW_TOURNAMENT["title"]
    assert datetime.fromisoformat(opened["starts_at"]) == datetime.fromisoformat(
        NEW_TOURNAMENT["starts_at"]
    )


def test_create_rejects_date_without_timezone(logged_in: TestClient) -> None:
    response = logged_in.post(
        "/tournaments", json={**NEW_TOURNAMENT, "starts_at": "2030-01-01T18:00"}
    )
    assert response.status_code == 422


def test_create_rejects_date_in_past(logged_in: TestClient) -> None:
    response = logged_in.post("/tournaments", json={**NEW_TOURNAMENT, "starts_at": in_days(-1)})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "starts_at"]


def test_create_rejects_blank_title(logged_in: TestClient) -> None:
    response = logged_in.post("/tournaments", json={**NEW_TOURNAMENT, "title": "   "})
    assert response.status_code == 422


def test_create_strips_title(logged_in: TestClient) -> None:
    response = logged_in.post("/tournaments", json={**NEW_TOURNAMENT, "title": "  Cup  "})
    assert response.status_code == 201
    assert response.json()["title"] == "Cup"


@pytest.mark.parametrize("max_teams", [4, 8, 16])
def test_create_accepts_bracket_sizes(logged_in: TestClient, max_teams: int) -> None:
    response = logged_in.post("/tournaments", json={**NEW_TOURNAMENT, "max_teams": max_teams})
    assert response.status_code == 201


@pytest.mark.parametrize("max_teams", [1, 2, 6, 32])
def test_create_rejects_other_team_counts(logged_in: TestClient, max_teams: int) -> None:
    response = logged_in.post("/tournaments", json={**NEW_TOURNAMENT, "max_teams": max_teams})
    assert response.status_code == 422


# --- список ---


def test_list_is_empty_without_tournaments(client: TestClient) -> None:
    assert client.get("/tournaments").json() == {"items": [], "total": 0}


def test_list_is_public_and_sorted_by_start(client: TestClient, db: Session, user: User) -> None:
    add_tournament(db, user, title="Later", starts_at=datetime.now(UTC) + timedelta(days=9))
    add_tournament(db, user, title="Sooner", starts_at=datetime.now(UTC) + timedelta(days=2))
    body = client.get("/tournaments").json()
    assert body["total"] == 2
    assert [item["title"] for item in body["items"]] == ["Sooner", "Later"]


def test_list_filters_by_status(client: TestClient, db: Session, user: User) -> None:
    add_tournament(db, user, title="Open", status="registration")
    add_tournament(db, user, title="Live", status="running")
    add_tournament(db, user, title="Done", status="finished")
    body = client.get("/tournaments", params={"status": ["running", "registration"]}).json()
    assert sorted(item["title"] for item in body["items"]) == ["Live", "Open"]


def test_teams_count_counts_only_approved(client: TestClient, db: Session, user: User) -> None:
    tournament = add_tournament(db, user)
    teams = [Team(name=f"T{i}", captain_id=user.id) for i in range(3)]
    db.add_all(teams)
    db.flush()
    for team, application in zip(teams, ["approved", "approved", "pending"], strict=True):
        db.add(TournamentTeam(tournament_id=tournament.id, team_id=team.id, status=application))
    db.commit()

    assert client.get("/tournaments").json()["items"][0]["teams_count"] == 2
    assert client.get(f"/tournaments/{tournament.id}").json()["teams_count"] == 2


# --- страница турнира ---


def test_get_unknown_tournament_is_404(client: TestClient) -> None:
    response = client.get("/tournaments/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Турнир не найден"}


def test_get_new_tournament_has_no_teams_or_bracket(
    client: TestClient, db: Session, user: User
) -> None:
    tournament = add_tournament(db, user, description="Осенний кубок")
    body = client.get(f"/tournaments/{tournament.id}").json()
    assert body["description"] == "Осенний кубок"
    assert body["teams"] == []
    assert body["matches"] == []


def test_get_tournament_has_teams_and_bracket(client: TestClient, db: Session, user: User) -> None:
    tournament = add_tournament(db, user, status="running")
    alpha, beta = Team(name="Alpha", captain_id=user.id), Team(name="Beta", captain_id=user.id)
    db.add_all([alpha, beta])
    db.flush()
    db.add_all(
        [
            TournamentTeam(tournament_id=tournament.id, team_id=beta.id, status="approved"),
            TournamentTeam(tournament_id=tournament.id, team_id=alpha.id, status="rejected"),
            Match(tournament_id=tournament.id, round=1, position=1, team1_id=alpha.id),
        ]
    )
    db.commit()

    body = client.get(f"/tournaments/{tournament.id}").json()
    assert body["teams"] == [
        {"id": alpha.id, "name": "Alpha", "status": "rejected"},
        {"id": beta.id, "name": "Beta", "status": "approved"},
    ]
    assert len(body["matches"]) == 1
    assert body["matches"][0]["team1_id"] == alpha.id
    assert body["matches"][0]["status"] == "scheduled"


# --- запуск пока заглушка ---


def test_start_tournament_is_still_a_stub(client: TestClient) -> None:
    response = client.post("/tournaments/7/start")
    assert response.status_code == 200
    assert response.json()["status"] == "running"
