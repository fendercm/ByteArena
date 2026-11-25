"""POST /tournaments/{id}/start: запуск турнира и построение сетки."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.security import ACCESS_TOKEN_COOKIE, create_access_token
from app.models.match import Match
from app.models.team import Team
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
from app.models.user import User


def add_tournament(
    db: Session, organizer: User, statuses: list[str], status: str = "closed"
) -> Tournament:
    """Турнир на 8 мест с заявками команд в указанных статусах."""
    tournament = Tournament(
        title="Cup",
        starts_at=datetime.now(UTC) + timedelta(days=3),
        max_teams=8,
        status=status,
        organizer_id=organizer.id,
    )
    db.add(tournament)
    db.flush()
    for index, team_status in enumerate(statuses, start=1):
        team = Team(name=f"Team {index}", captain_id=organizer.id)
        db.add(team)
        db.flush()
        db.add(TournamentTeam(tournament_id=tournament.id, team_id=team.id, status=team_status))
    db.commit()
    return tournament


def matches_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Match))


def test_start_builds_bracket_and_runs_tournament(
    logged_in: TestClient, db: Session, user: User
) -> None:
    tournament = add_tournament(db, user, ["approved"] * 5 + ["rejected"])

    response = logged_in.post(f"/tournaments/{tournament.id}/start")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert body["teams_count"] == 5
    # 5 команд -> 8 мест: 7 матчей, из них 3 прохода без игры, уже сыгранных
    assert len(body["matches"]) == 7
    byes = [m for m in body["matches"] if m["round"] == 1 and m["team2_id"] is None]
    assert len(byes) == 3
    assert all(m["status"] == "finished" and m["winner_id"] == m["team1_id"] for m in byes)
    # та же сетка видна на странице турнира
    page = logged_in.get(f"/tournaments/{tournament.id}").json()
    assert page["status"] == "running"
    assert page["matches"] == body["matches"]


def test_two_teams_play_only_final(logged_in: TestClient, db: Session, user: User) -> None:
    tournament = add_tournament(db, user, ["approved", "approved"])

    matches = logged_in.post(f"/tournaments/{tournament.id}/start").json()["matches"]

    assert len(matches) == 1
    assert matches[0]["status"] == "scheduled"
    assert matches[0]["next_match_id"] is None


@pytest.mark.parametrize("status", ["draft", "registration"])
def test_start_needs_closed_registration(
    logged_in: TestClient, db: Session, user: User, status: str
) -> None:
    tournament = add_tournament(db, user, ["approved"] * 4, status=status)

    response = logged_in.post(f"/tournaments/{tournament.id}/start")

    assert response.status_code == 409
    assert response.json() == {"detail": "Регистрация ещё не закрыта"}
    assert matches_count(db) == 0


def test_second_start_is_409(logged_in: TestClient, db: Session, user: User) -> None:
    tournament = add_tournament(db, user, ["approved"] * 4)
    assert logged_in.post(f"/tournaments/{tournament.id}/start").status_code == 200

    response = logged_in.post(f"/tournaments/{tournament.id}/start")

    assert response.status_code == 409
    assert response.json() == {"detail": "Турнир уже запущен"}
    assert matches_count(db) == 3  # сетка не построилась второй раз


def test_finished_tournament_cannot_start(logged_in: TestClient, db: Session, user: User) -> None:
    tournament = add_tournament(db, user, ["approved"] * 4, status="finished")

    response = logged_in.post(f"/tournaments/{tournament.id}/start")

    assert response.status_code == 409
    assert response.json() == {"detail": "Турнир уже запущен"}


def test_start_requires_login(client: TestClient, db: Session, user: User) -> None:
    tournament = add_tournament(db, user, ["approved"] * 4)

    assert client.post(f"/tournaments/{tournament.id}/start").status_code == 401


def test_only_organizer_starts(client: TestClient, db: Session, user: User) -> None:
    tournament = add_tournament(db, user, ["approved"] * 4)
    other = User(discord_id="200", nickname="Stranger")
    db.add(other)
    db.commit()
    client.cookies.set(ACCESS_TOKEN_COOKIE, create_access_token(other.id))

    response = client.post(f"/tournaments/{tournament.id}/start")

    assert response.status_code == 403
    assert response.json() == {"detail": "Это может только организатор турнира"}
    assert db.get(Tournament, tournament.id).status == "closed"
    assert matches_count(db) == 0


def test_unknown_tournament_is_404(logged_in: TestClient) -> None:
    response = logged_in.post("/tournaments/999/start")

    assert response.status_code == 404
    assert response.json() == {"detail": "Турнир не найден"}
