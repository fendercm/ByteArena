from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.security import ACCESS_TOKEN_COOKIE, create_access_token
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
from app.models.user import User


def add_tournament(db: Session, organizer: User, max_teams: int = 4, **fields) -> Tournament:
    tournament = Tournament(
        title="Cup",
        starts_at=datetime.now(UTC) + timedelta(days=3),
        max_teams=max_teams,
        status=fields.pop("status", "registration"),
        organizer_id=organizer.id,
        **fields,
    )
    db.add(tournament)
    db.commit()
    return tournament


def add_registration(
    db: Session, tournament: Tournament, name: str, status: str = "pending"
) -> TournamentTeam:
    """Команда со смешанным составом (капитан с аккаунтом + ники без аккаунта) и её заявка."""
    captain = User(discord_id=f"captain-{name}", nickname=f"{name} Captain")
    db.add(captain)
    db.flush()
    team = Team(name=name, captain_id=captain.id)
    db.add(team)
    db.flush()
    db.add_all(
        [
            TeamMember(
                team_id=team.id, user_id=captain.id, nickname=captain.nickname, role="captain"
            ),
            TeamMember(team_id=team.id, nickname=f"{name} Sub", role="sub"),
            TeamMember(team_id=team.id, nickname=f"{name} Main", role="main"),
        ]
    )
    registration = TournamentTeam(tournament_id=tournament.id, team_id=team.id, status=status)
    db.add(registration)
    db.commit()
    return registration


@pytest.fixture
def stranger(client: TestClient, db: Session) -> TestClient:
    """Клиент, вошедший как другой игрок — не организатор."""
    other = User(discord_id="200", nickname="Stranger")
    db.add(other)
    db.commit()
    stranger_client = TestClient(client.app, follow_redirects=False)
    stranger_client.cookies.set(ACCESS_TOKEN_COOKIE, create_access_token(other.id))
    return stranger_client


# --- GET /tournaments/{id}/registrations ---


def test_organizer_sees_all_registrations_with_rosters(
    logged_in: TestClient, db: Session, user: User
) -> None:
    tournament = add_tournament(db, user)
    first = add_registration(db, tournament, "Alpha", "approved")
    add_registration(db, tournament, "Beta", "rejected")
    add_registration(db, tournament, "Gamma")

    body = logged_in.get(f"/tournaments/{tournament.id}/registrations").json()
    assert body["total"] == 3
    assert [item["team"]["name"] for item in body["items"]] == ["Alpha", "Beta", "Gamma"]
    assert [item["status"] for item in body["items"]] == ["approved", "rejected", "pending"]

    alpha = body["items"][0]
    assert alpha["id"] == first.id
    assert alpha["members"][0] == {
        "nickname": "Alpha Captain",
        "user_id": first_team_captain_id(db, first),
        "role": "captain",
    }
    # ник без аккаунта приходит с user_id = null; порядок: капитан, основные, запасные
    assert [(m["nickname"], m["user_id"], m["role"]) for m in alpha["members"][1:]] == [
        ("Alpha Main", None, "main"),
        ("Alpha Sub", None, "sub"),
    ]


def first_team_captain_id(db: Session, registration: TournamentTeam) -> int:
    return db.get(Team, registration.team_id).captain_id


def test_registrations_require_login(client: TestClient, db: Session, user: User) -> None:
    tournament = add_tournament(db, user)
    assert client.get(f"/tournaments/{tournament.id}/registrations").status_code == 401


def test_registrations_are_hidden_from_others(
    stranger: TestClient, db: Session, user: User
) -> None:
    tournament = add_tournament(db, user)
    response = stranger.get(f"/tournaments/{tournament.id}/registrations")
    assert response.status_code == 403
    assert response.json() == {"detail": "Это может только организатор турнира"}


def test_registrations_of_unknown_tournament_is_404(logged_in: TestClient) -> None:
    assert logged_in.get("/tournaments/999/registrations").status_code == 404


# --- PATCH /registrations/{id} ---


def test_approve_and_reject(logged_in: TestClient, db: Session, user: User) -> None:
    tournament = add_tournament(db, user)
    registration = add_registration(db, tournament, "Alpha")

    response = logged_in.patch(f"/registrations/{registration.id}", json={"status": "approved"})
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["team"]["name"] == "Alpha"
    assert logged_in.get(f"/tournaments/{tournament.id}").json()["teams_count"] == 1

    response = logged_in.patch(f"/registrations/{registration.id}", json={"status": "rejected"})
    assert response.json()["status"] == "rejected"
    assert logged_in.get(f"/tournaments/{tournament.id}").json()["teams_count"] == 0


def test_cannot_approve_more_than_max_teams(logged_in: TestClient, db: Session, user: User) -> None:
    tournament = add_tournament(db, user, max_teams=4)
    for name in ["A", "B", "C", "D"]:
        add_registration(db, tournament, name, "approved")
    fifth = add_registration(db, tournament, "E")

    response = logged_in.patch(f"/registrations/{fifth.id}", json={"status": "approved"})
    assert response.status_code == 409
    assert response.json() == {"detail": "Мест нет"}
    # отклонить при полном турнире можно
    rejected = logged_in.patch(f"/registrations/{fifth.id}", json={"status": "rejected"})
    assert rejected.status_code == 200


def test_reapproving_approved_team_in_full_tournament_is_ok(
    logged_in: TestClient, db: Session, user: User
) -> None:
    tournament = add_tournament(db, user, max_teams=4)
    registrations = [add_registration(db, tournament, n, "approved") for n in "ABCD"]
    response = logged_in.patch(f"/registrations/{registrations[0].id}", json={"status": "approved"})
    assert response.status_code == 200


def test_only_organizer_decides(stranger: TestClient, db: Session, user: User) -> None:
    registration = add_registration(db, add_tournament(db, user), "Alpha")
    response = stranger.patch(f"/registrations/{registration.id}", json={"status": "approved"})
    assert response.status_code == 403
    assert db.get(TournamentTeam, registration.id).status == "pending"


def test_decision_status_must_be_approved_or_rejected(
    logged_in: TestClient, db: Session, user: User
) -> None:
    registration = add_registration(db, add_tournament(db, user), "Alpha")
    response = logged_in.patch(f"/registrations/{registration.id}", json={"status": "pending"})
    assert response.status_code == 422


def test_unknown_registration_is_404(logged_in: TestClient) -> None:
    response = logged_in.patch("/registrations/999", json={"status": "approved"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Заявка не найдена"}


def test_no_decisions_after_registration_closed(
    logged_in: TestClient, db: Session, user: User
) -> None:
    tournament = add_tournament(db, user, status="closed")
    registration = add_registration(db, tournament, "Alpha")
    response = logged_in.patch(f"/registrations/{registration.id}", json={"status": "approved"})
    assert response.status_code == 409
    assert response.json() == {"detail": "Регистрация закрыта"}


# --- POST /tournaments/{id}/close-registration ---


def test_close_registration(logged_in: TestClient, db: Session, user: User) -> None:
    tournament = add_tournament(db, user)
    add_registration(db, tournament, "Alpha", "approved")
    add_registration(db, tournament, "Beta", "approved")
    add_registration(db, tournament, "Gamma")

    response = logged_in.post(f"/tournaments/{tournament.id}/close-registration")
    assert response.status_code == 200
    assert response.json()["status"] == "closed"
    assert response.json()["teams_count"] == 2

    closed = logged_in.get("/tournaments", params={"status": "closed"}).json()
    assert [item["id"] for item in closed["items"]] == [tournament.id]


def test_close_needs_two_approved_teams(logged_in: TestClient, db: Session, user: User) -> None:
    tournament = add_tournament(db, user)
    add_registration(db, tournament, "Alpha", "approved")
    add_registration(db, tournament, "Beta")

    response = logged_in.post(f"/tournaments/{tournament.id}/close-registration")
    assert response.status_code == 409
    assert response.json() == {"detail": "Нужно минимум 2 подтверждённые команды"}
    assert db.get(Tournament, tournament.id).status == "registration"


def test_close_twice_is_409(logged_in: TestClient, db: Session, user: User) -> None:
    tournament = add_tournament(db, user, status="closed")
    response = logged_in.post(f"/tournaments/{tournament.id}/close-registration")
    assert response.status_code == 409
    assert response.json() == {"detail": "Регистрация уже закрыта"}


def test_only_organizer_closes(stranger: TestClient, db: Session, user: User) -> None:
    tournament = add_tournament(db, user)
    assert stranger.post(f"/tournaments/{tournament.id}/close-registration").status_code == 403
    assert db.get(Tournament, tournament.id).status == "registration"
