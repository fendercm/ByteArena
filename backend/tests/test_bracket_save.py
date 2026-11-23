import random
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.team import Team
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
from app.models.user import User
from app.services.bracket import BracketError, next_slot, save_bracket


def add_tournament(db: Session, organizer: User, status: str = "closed") -> Tournament:
    tournament = Tournament(
        title="Cup",
        starts_at=datetime.now(UTC) + timedelta(days=3),
        max_teams=8,
        status=status,
        organizer_id=organizer.id,
    )
    db.add(tournament)
    db.commit()
    return tournament


def add_teams(db: Session, tournament: Tournament, captain: User, statuses: list[str]) -> list[int]:
    """Команды с заявками в указанных статусах; возвращает id подтверждённых."""
    approved = []
    for index, status in enumerate(statuses, start=1):
        team = Team(name=f"Team {index}", captain_id=captain.id)
        db.add(team)
        db.flush()
        db.add(TournamentTeam(tournament_id=tournament.id, team_id=team.id, status=status))
        if status == "approved":
            approved.append(team.id)
    db.commit()
    return approved


def test_five_teams_bracket_is_saved_with_links(db: Session, user: User) -> None:
    tournament = add_tournament(db, user)
    approved = add_teams(db, tournament, user, ["approved"] * 5 + ["pending", "rejected"])

    saved = save_bracket(db, tournament, rng=random.Random(1))
    db.commit()

    matches = db.scalars(
        select(Match)
        .where(Match.tournament_id == tournament.id)
        .order_by(Match.round, Match.position)
    ).all()
    assert [m.id for m in matches] == [m.id for m in saved]
    assert len(matches) == 7

    # в первом раунде ровно подтверждённые команды, по одному разу
    first_round = [t for m in matches if m.round == 1 for t in (m.team1_id, m.team2_id) if t]
    assert sorted(first_round) == sorted(approved)

    # три прохода без игры: завершены, победитель — единственная команда
    byes = [m for m in matches if m.round == 1 and m.team2_id is None]
    assert len(byes) == 3
    assert all(m.status == "finished" and m.winner_id == m.team1_id for m in byes)
    assert all(m.status == "scheduled" for m in matches if m not in byes)

    # каждый матч ведёт в нужный матч следующего раунда, у финала next_match_id пустой
    by_place = {(m.round, m.position): m for m in matches}
    for m in matches:
        target = by_place.get(next_slot(m.round, m.position)[:2])
        assert m.next_match_id == (target.id if target else None)
    assert [m for m in matches if m.next_match_id is None] == [by_place[(3, 1)]]

    # победители bye уже стоят во втором раунде
    for m in byes:
        r2, p2, slot = next_slot(m.round, m.position)
        assert getattr(by_place[(r2, p2)], slot) == m.winner_id


def test_order_of_teams_is_shuffled(db: Session, user: User) -> None:
    pairs = set()
    for seed in range(5):
        tournament = add_tournament(db, user)
        approved = add_teams(db, tournament, user, ["approved"] * 4)
        matches = save_bracket(db, tournament, rng=random.Random(seed))
        first = [approved.index(m.team1_id) for m in matches if m.round == 1]
        pairs.add(tuple(first))
    assert len(pairs) > 1


def test_saved_bracket_is_visible_on_tournament_page(
    client: TestClient, db: Session, user: User
) -> None:
    tournament = add_tournament(db, user)
    add_teams(db, tournament, user, ["approved"] * 6)
    save_bracket(db, tournament)
    db.commit()

    body = client.get(f"/tournaments/{tournament.id}").json()
    assert len(body["matches"]) == 7
    assert sum(m["status"] == "finished" for m in body["matches"]) == 2


@pytest.mark.parametrize("status", ["draft", "registration", "running", "finished"])
def test_only_closed_tournament_gets_bracket(db: Session, user: User, status: str) -> None:
    tournament = add_tournament(db, user, status=status)
    add_teams(db, tournament, user, ["approved"] * 4)
    with pytest.raises(BracketError, match="после закрытия регистрации"):
        save_bracket(db, tournament)


def test_bracket_is_built_once(db: Session, user: User) -> None:
    tournament = add_tournament(db, user)
    add_teams(db, tournament, user, ["approved"] * 4)
    save_bracket(db, tournament)
    db.commit()
    with pytest.raises(BracketError, match="уже построена"):
        save_bracket(db, tournament)
    assert db.scalar(select(func.count()).select_from(Match)) == 3


def test_needs_two_approved_teams(db: Session, user: User) -> None:
    tournament = add_tournament(db, user)
    add_teams(db, tournament, user, ["approved", "pending", "rejected"])
    with pytest.raises(BracketError, match="минимум 2 подтверждённые команды"):
        save_bracket(db, tournament)
