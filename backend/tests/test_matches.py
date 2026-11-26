from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.match import Match
from app.models.team import Team
from app.models.tournament import Tournament
from app.models.user import User

client = TestClient(app)


def test_get_match_has_team_names(db: Session) -> None:
    organizer = User(discord_id="match-organizer", nickname="Organizer")
    db.add(organizer)
    db.flush()
    tournament = Tournament(
        title="Cup",
        starts_at=datetime.now(UTC) + timedelta(days=3),
        max_teams=4,
        status="running",
        organizer_id=organizer.id,
    )
    db.add(tournament)
    db.flush()
    team1 = Team(name="Night Wolves", captain_id=organizer.id)
    team2 = Team(name="Frostbyte", captain_id=organizer.id)
    db.add_all([team1, team2])
    db.flush()
    match = Match(
        tournament_id=tournament.id,
        round=1,
        position=1,
        team1_id=team1.id,
        team2_id=team2.id,
        score1=13,
        score2=8,
        winner_id=team1.id,
        status="finished",
        scheduled_at=datetime.now(UTC),
        next_match_id=None,
    )
    db.add(match)
    db.commit()

    response = client.get(f"/matches/{match.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == match.id
    assert body["tournament_id"] == tournament.id
    assert body["team1"] == {"id": team1.id, "name": "Night Wolves"}
    assert body["team2"] == {"id": team2.id, "name": "Frostbyte"}
    assert body["score1"] == 13
    assert body["score2"] == 8
    assert body["winner_id"] == team1.id


def test_get_unknown_match_is_404(db: Session) -> None:
    response = client.get("/matches/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Матч не найден"}
