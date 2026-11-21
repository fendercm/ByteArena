from datetime import UTC, datetime

from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
from app.models.user import User

TEAM = {
    "name": "Night Wolves",
    "members": [
        {"nickname": "Alpha", "user_id": 2, "role": "main"},
        {"nickname": "Bravo", "user_id": 3, "role": "main"},
        {"nickname": "Charlie", "role": "main"},
        {"nickname": "Delta", "user_id": 5, "role": "main"},
        {"nickname": "Echo", "role": "sub"},
    ],
}


def test_create_team_with_member_roles(logged_in, db) -> None:
    db.add_all(
        [
            User(discord_id="201", nickname="Verified Alpha"),
            User(discord_id="202", nickname="Verified Bravo"),
            User(discord_id="203", nickname="Unused Player"),
            User(discord_id="204", nickname="Verified Delta"),
        ]
    )
    db.commit()

    response = logged_in.post("/teams", json=TEAM, headers={"X-User-Id": "999"})
    assert response.status_code == 201
    body = response.json()
    assert body["captain_id"] == 1
    assert [member["role"] for member in body["members"]] == [
        "captain",
        "main",
        "main",
        "main",
        "main",
        "sub",
    ]
    assert body["members"][0] == {"nickname": "Organizer", "user_id": 1, "role": "captain"}
    assert body["members"][3]["user_id"] is None
    assert body["members"][1]["nickname"] == "Verified Alpha"
    assert body["members"][2]["nickname"] == "Verified Bravo"
    assert body["members"][4]["nickname"] == "Verified Delta"

    team = db.get(Team, body["id"])
    assert team is not None
    assert team.name == TEAM["name"]
    assert len(db.query(TeamMember).filter_by(team_id=team.id).all()) == 6


def test_get_team_returns_captain_members_and_tournaments(client, db, user) -> None:
    player = User(
        discord_id="team-member-1",
        nickname="Verified Player",
        avatar_url="https://example.com/avatar.png",
    )
    db.add(player)
    db.flush()

    team = Team(name="Night Wolves", captain_id=user.id)
    db.add(team)
    db.flush()
    db.add_all(
        [
            TeamMember(team_id=team.id, user_id=user.id, nickname=user.nickname, role="captain"),
            TeamMember(team_id=team.id, user_id=player.id, nickname=player.nickname, role="main"),
            TeamMember(team_id=team.id, user_id=None, nickname="Offline Player", role="sub"),
        ]
    )
    tournament = Tournament(
        title="Autumn Championship",
        starts_at=datetime(2026, 12, 1, 18, 0, tzinfo=UTC),
        max_teams=8,
        organizer_id=user.id,
        status="closed",
    )
    db.add(tournament)
    db.flush()
    db.add(TournamentTeam(tournament_id=tournament.id, team_id=team.id, status="approved"))
    db.commit()

    response = client.get(f"/teams/{team.id}")

    assert response.status_code == 200
    profile = response.json()
    assert profile["id"] == team.id
    assert profile["name"] == "Night Wolves"
    assert profile["captain"] == {"id": user.id, "nickname": "Organizer"}
    assert [member["role"] for member in profile["members"]] == ["captain", "main", "sub"]
    assert profile["members"][1] == {
        "nickname": "Verified Player",
        "user_id": player.id,
        "avatar_url": "https://example.com/avatar.png",
        "role": "main",
    }
    assert profile["members"][2]["user_id"] is None
    assert profile["members"][2]["avatar_url"] is None
    assert profile["tournaments"] == [
        {
            "id": tournament.id,
            "title": "Autumn Championship",
            "starts_at": "2026-12-01T18:00:00Z",
            "status": "closed",
            "application_status": "approved",
        }
    ]


def test_get_unknown_team_returns_404(client) -> None:
    response = client.get("/teams/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Команда не найдена"}


def test_create_team_requires_login(client) -> None:
    response = client.post("/teams", json=TEAM)
    assert response.status_code == 401
    assert response.json() == {"detail": "Сначала войдите через Discord"}


def test_create_team_rejects_unknown_member_user_id(logged_in) -> None:
    response = logged_in.post(
        "/teams",
        json={**TEAM, "members": [{**TEAM["members"][0], "user_id": 9999}, *TEAM["members"][1:]]},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Игрок с ID 9999 не найден"}


def test_create_team_rejects_captain_nickname_duplicate(logged_in) -> None:
    members = [
        {**TEAM["members"][0], "nickname": "organizer", "user_id": None},
        *TEAM["members"][1:],
    ]

    response = logged_in.post("/teams", json={**TEAM, "members": members})

    assert response.status_code == 400
    assert response.json() == {"detail": "Ник капитана не должен повторяться в составе"}


def test_create_team_validates_name_roster_and_unique_nicknames(logged_in) -> None:
    assert logged_in.post("/teams", json={**TEAM, "name": "A"}).status_code == 422
    assert logged_in.post("/teams", json={**TEAM, "name": "  "}).status_code == 422
    assert logged_in.post("/teams", json={**TEAM, "name": "x" * 33}).status_code == 422
    whitespace_nickname = {
        **TEAM,
        "members": [{**TEAM["members"][0], "nickname": "  "}, *TEAM["members"][1:]],
    }
    assert logged_in.post("/teams", json=whitespace_nickname).status_code == 422
    assert (
        logged_in.post("/teams", json={**TEAM, "members": TEAM["members"][:3]}).status_code == 422
    )
    duplicate = {
        **TEAM,
        "members": [
            TEAM["members"][0],
            {**TEAM["members"][1], "nickname": "alpha"},
            *TEAM["members"][2:],
        ],
    }
    assert logged_in.post("/teams", json=duplicate).status_code == 422
    too_many_subs = {
        **TEAM,
        "members": [
            *TEAM["members"],
            {"nickname": "Foxtrot", "role": "sub"},
            {"nickname": "Golf", "role": "sub"},
        ],
    }
    assert logged_in.post("/teams", json=too_many_subs).status_code == 422


def test_tournament_teams_returns_fake_teams(client) -> None:
    response = client.get("/tournaments/8/teams")
    assert response.status_code == 200
    body = response.json()
    assert 2 <= len(body["items"]) <= 3
    assert body["total"] == len(body["items"])
    assert all(team["members"] for team in body["items"])


def test_register_team_for_tournament_requires_login(client) -> None:
    unauthorized = client.post("/tournaments/8/registrations", json={"team_id": 5})
    assert unauthorized.status_code == 401


def test_register_team_for_tournament_uses_authenticated_user(logged_in) -> None:
    response = logged_in.post("/tournaments/8/registrations", json={"team_id": 5})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "tournament_id": 8, "team_id": 5, "status": "pending"}


def test_my_registration_requires_login(client) -> None:
    assert client.get("/tournaments/8/my-registration").status_code == 401


def test_my_registration_uses_authenticated_user(logged_in) -> None:
    response = logged_in.get("/tournaments/8/my-registration", headers={"X-User-Id": "999"})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "tournament_id": 8, "team_id": 1, "status": "approved"}
