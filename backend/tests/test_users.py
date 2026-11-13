from datetime import UTC, datetime

from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam


def test_me_requires_login(client) -> None:
    response = client.get("/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Сначала войдите через Discord"}


def test_get_user_profile_returns_database_data(client, db, user) -> None:
    team = Team(name="Night Wolves", captain_id=user.id)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=user.id, role="captain"))

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
    assert profile["tournaments"] == [
        {"id": tournament.id, "title": "Autumn Championship"}
    ]


def test_get_unknown_user_returns_404(client) -> None:
    response = client.get("/users/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Игрок не найден"}
