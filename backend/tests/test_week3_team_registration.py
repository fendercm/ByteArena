from datetime import UTC, datetime, timedelta

import pytest

from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
from app.models.user import User


@pytest.fixture
def player(db):
    account = User(discord_id="101", nickname="kolya")
    db.add(account)
    db.commit()
    return account


@pytest.fixture
def roster(player):
    return [
        {"nickname": player.nickname, "user_id": player.id, "role": "main"},
        *[{"nickname": nickname, "role": "main"} for nickname in ("Petya", "Mira", "Nova")],
    ]


def create_team(client, roster):
    return client.post("/teams", json={"name": "Arena Five", "members": roster})


def seed_team(db, captain, name, player=None):
    team = Team(name=name, captain_id=captain.id)
    db.add(team)
    db.flush()
    db.add(
        TeamMember(team_id=team.id, nickname=captain.nickname, user_id=captain.id, role="captain")
    )
    if player:
        db.add(
            TeamMember(team_id=team.id, nickname=player.nickname, user_id=player.id, role="main")
        )
    db.flush()
    return team


@pytest.fixture
def registration_setup(db, user, player):
    tournament = Tournament(
        title="Кубок",
        organizer_id=user.id,
        starts_at=datetime.now(UTC) + timedelta(days=1),
        max_teams=4,
        status="registration",
    )
    db.add(tournament)
    team = seed_team(db, user, "Arena Five", player)
    db.commit()
    return tournament, team


def register(client, tournament, team):
    return client.post(f"/tournaments/{tournament.id}/registrations", json={"team_id": team.id})


def assert_denied(response, status, detail):
    assert response.status_code == status
    assert detail in response.json()["detail"]


def test_mixed_team_with_two_substitutes(logged_in, roster, user, player):
    roster += [{"nickname": nickname, "role": "sub"} for nickname in ("Echo", "Flash")]
    response = create_team(logged_in, roster)
    assert response.status_code == 201
    body = response.json()
    assert body["captain_id"] == user.id
    assert len(body["members"]) == 7
    assert any(member["user_id"] == player.id for member in body["members"])
    assert any(
        member["nickname"] == "Petya" and member["user_id"] is None for member in body["members"]
    )


def test_team_requires_four_main_players(logged_in, roster):
    members = [*roster[:3], {"nickname": "Echo", "role": "sub"}]
    assert create_team(logged_in, members).status_code == 422


def test_team_rejects_three_substitutes(logged_in, roster):
    roster += [{"nickname": name, "role": "sub"} for name in ("Echo", "Flash", "Blaze")]
    assert create_team(logged_in, roster).status_code == 422


def test_duplicate_nickname_ignores_case(logged_in, roster):
    roster[2]["nickname"] = "petya"
    assert create_team(logged_in, roster).status_code == 422


def test_team_rejects_unknown_player(logged_in, roster):
    roster[0]["user_id"] = 999999
    assert create_team(logged_in, roster).status_code in (404, 422)


def test_search_matches_prefix_and_requires_two_characters(client, player):
    short = client.get("/users/search", params={"q": "k"})
    assert short.status_code == 200
    assert short.json() == []
    response = client.get("/users/search", params={"q": "ko"})
    assert response.status_code == 200
    assert player.id in {item["id"] for item in response.json()}
    assert all(item["nickname"].lower().startswith("ko") for item in response.json())


def test_captain_sends_pending_registration(logged_in, registration_setup):
    tournament, team = registration_setup
    response = register(logged_in, tournament, team)
    assert response.status_code == 201
    body = response.json()
    assert (body["tournament_id"], body["team_id"], body["status"]) == (
        tournament.id,
        team.id,
        "pending",
    )


def test_registration_requires_captain(logged_in, db, player, registration_setup):
    tournament, _ = registration_setup
    other = seed_team(db, player, "Other")
    db.commit()
    assert_denied(register(logged_in, tournament, other), 403, "капитан")


def test_team_cannot_register_twice(logged_in, db, registration_setup):
    tournament, team = registration_setup
    db.add(TournamentTeam(tournament_id=tournament.id, team_id=team.id, status="pending"))
    db.commit()
    assert_denied(register(logged_in, tournament, team), 409, "уже подала заявку")


def test_closed_tournament_rejects_registration(logged_in, db, registration_setup):
    tournament, team = registration_setup
    tournament.status = "closed"
    db.commit()
    assert_denied(register(logged_in, tournament, team), 409, "Регистрация закрыта")


def test_full_tournament_rejects_registration(logged_in, db, user, registration_setup):
    tournament, team = registration_setup
    for i in range(tournament.max_teams):
        other = seed_team(db, user, f"Approved {i}")
        db.add(TournamentTeam(tournament_id=tournament.id, team_id=other.id, status="approved"))
    db.commit()
    assert_denied(register(logged_in, tournament, team), 409, "Мест нет")


def test_registered_player_cannot_join_another_team(logged_in, db, player, registration_setup):
    tournament, team = registration_setup
    other_captain = User(discord_id="102", nickname="OtherCaptain")
    db.add(other_captain)
    db.flush()
    other = seed_team(db, other_captain, "Other", player)
    db.add(TournamentTeam(tournament_id=tournament.id, team_id=other.id, status="approved"))
    db.commit()
    assert_denied(register(logged_in, tournament, team), 409, player.nickname)
