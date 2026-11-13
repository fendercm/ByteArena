from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Team, TeamMember, Tournament, TournamentTeam, User
from app.seed import seed_data


def test_seed_is_repeatable_and_keeps_existing_data(db: Session) -> None:
    existing = User(discord_id="real-player", nickname="Real player")
    db.add(existing)
    db.commit()

    created = seed_data(db)
    db.commit()
    assert created == dict(users=41, teams=8, members=40, tournaments=6, registrations=42)
    first_dates = list(db.scalars(select(Tournament.starts_at).order_by(Tournament.id)))

    assert seed_data(db) == dict(users=0, teams=0, members=0, tournaments=0, registrations=0)
    db.commit()
    assert db.scalar(select(func.count()).select_from(User)) == 42
    assert existing.nickname == "Real player"
    assert list(db.scalars(select(Tournament.starts_at).order_by(Tournament.id))) == first_dates
    assert db.scalar(select(func.count()).select_from(TeamMember)) == 40
    assert db.scalar(select(func.count()).select_from(Team)) == 8
    assert db.scalar(select(func.count()).select_from(TournamentTeam)) == 42


def test_seed_tournaments_are_available_through_api(client, db: Session) -> None:
    seed_data(db)
    db.commit()
    running = client.get("/tournaments?status=running").json()["items"]
    upcoming = client.get("/tournaments?status=registration").json()["items"]
    assert len(running) == 2
    assert len(upcoming) == 3
    assert [t["teams_count"] for t in upcoming] == [6, 4, 8]
    assert all(t["starts_at"].endswith("Z") for t in running + upcoming)


def test_seed_can_be_rolled_back_as_one_transaction(db: Session) -> None:
    seed_data(db)
    db.rollback()
    for model in (User, Team, TeamMember, Tournament, TournamentTeam):
        assert db.scalar(select(func.count()).select_from(model)) == 0
