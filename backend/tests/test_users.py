from datetime import UTC, datetime

from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
from app.models.user import User


def test_user_search_returns_database_prefix_matches(client, db) -> None:
    for index, nickname in enumerate(["Alpine", "alpha", "Alfred", "Malice"], start=1):
        db.add(User(discord_id=f"search-{index}", nickname=nickname))
    db.commit()

    assert client.get("/users/search", params={"q": " a "}).json() == []
    response = client.get("/users/search", params={"q": "  aL  "})
    assert response.status_code == 200
    assert [item["nickname"] for item in response.json()] == ["Alfred", "Alpine", "alpha"]
    assert all(set(item) == {"id", "nickname", "avatar_url"} for item in response.json())


def test_user_search_escapes_like_wildcards_and_limits_results(client, db) -> None:
    nicknames = ["A%player", "Abplayer", *[f"Test{index:02}" for index in range(12)]]
    for index, nickname in enumerate(nicknames, start=1):
        db.add(User(discord_id=f"search-limit-{index}", nickname=nickname))
    db.commit()

    wildcard_response = client.get("/users/search", params={"q": "A%"})
    assert wildcard_response.status_code == 200
    assert [item["nickname"] for item in wildcard_response.json()] == ["A%player"]

    limited_response = client.get("/users/search", params={"q": "test"})
    assert limited_response.status_code == 200
    assert len(limited_response.json()) == 10


def test_user_search_returns_empty_list_when_database_has_no_match(client) -> None:
    response = client.get("/users/search", params={"q": "fe"})

    assert response.status_code == 200
    assert response.json() == []


def test_me_requires_login(client) -> None:
    response = client.get("/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Сначала войдите через Discord"}


def test_me_returns_team_of_logged_in_user(client, db, user, logged_in) -> None:
    assert client.get("/me").json()["team"] is None

    team = Team(name="Night Wolves", captain_id=user.id)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=user.id, nickname=user.nickname, role="captain"))
    db.commit()

    response = client.get("/me")
    assert response.status_code == 200
    assert response.json() == {
        "id": user.id,
        "nickname": "Organizer",
        "avatar_url": None,
        "team": {"id": team.id, "name": "Night Wolves"},
    }


def test_get_user_profile_returns_database_data(client, db, user) -> None:
    team = Team(name="Night Wolves", captain_id=user.id)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=user.id, nickname=user.nickname, role="captain"))

    tournament = Tournament(
        title="Autumn Championship",
        starts_at=datetime(2026, 12, 1, 18, 0, tzinfo=UTC),
        max_teams=4,
        organizer_id=user.id,
        status="registration",
    )
    db.add(tournament)
    db.flush()
    db.add(
        TournamentTeam(
            tournament_id=tournament.id,
            team_id=team.id,
            status="approved",
        )
    )
    db.commit()

    response = client.get(f"/users/{user.id}")

    assert response.status_code == 200
    profile = response.json()
    assert profile["id"] == user.id
    assert profile["nickname"] == "Organizer"
    assert profile["team"] == {"id": team.id, "name": "Night Wolves"}
    assert profile["tournaments"] == [{"id": tournament.id, "title": "Autumn Championship"}]


def test_get_unknown_user_returns_404(client) -> None:
    response = client.get("/users/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Игрок не найден"}
