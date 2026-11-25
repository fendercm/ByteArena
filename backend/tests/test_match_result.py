"""POST /matches/{id}/result: счёт, переход победителя и исправление результата."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.security import ACCESS_TOKEN_COOKIE, create_access_token
from app.models.team import Team
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
from app.models.user import User

Bracket = dict[tuple[int, int], dict]


def start_tournament(client: TestClient, db: Session, organizer: User, teams: int) -> int:
    """Закрытый турнир с подтверждёнными командами, запущенный через API. Возвращает id."""
    tournament = Tournament(
        title="Cup",
        starts_at=datetime.now(UTC) + timedelta(days=3),
        max_teams=8,
        status="closed",
        organizer_id=organizer.id,
    )
    db.add(tournament)
    db.flush()
    for index in range(1, teams + 1):
        team = Team(name=f"Team {index}", captain_id=organizer.id)
        db.add(team)
        db.flush()
        db.add(TournamentTeam(tournament_id=tournament.id, team_id=team.id, status="approved"))
    db.commit()
    assert client.post(f"/tournaments/{tournament.id}/start").status_code == 200
    return tournament.id


def bracket(client: TestClient, tournament_id: int) -> Bracket:
    """Матчи турнира по месту в сетке: (раунд, позиция) -> матч."""
    matches = client.get(f"/tournaments/{tournament_id}").json()["matches"]
    return {(m["round"], m["position"]): m for m in matches}


def result(client: TestClient, match_id: int, score1: int, score2: int):
    return client.post(f"/matches/{match_id}/result", json={"score1": score1, "score2": score2})


def test_winner_goes_to_next_match(logged_in: TestClient, db: Session, user: User) -> None:
    tournament_id = start_tournament(logged_in, db, user, teams=4)
    before = bracket(logged_in, tournament_id)

    first = result(logged_in, before[(1, 1)]["id"], 13, 8)
    second = result(logged_in, before[(1, 2)]["id"], 5, 13)

    assert first.status_code == 200
    assert first.json()["status"] == "finished"
    assert first.json()["winner_id"] == before[(1, 1)]["team1_id"]
    after = bracket(logged_in, tournament_id)
    # победитель нечётной позиции становится team1 следующего матча, чётной — team2
    assert after[(2, 1)]["team1_id"] == before[(1, 1)]["team1_id"]
    assert after[(2, 1)]["team2_id"] == second.json()["winner_id"] == before[(1, 2)]["team2_id"]
    assert after[(1, 1)]["score1"] == 13 and after[(1, 1)]["score2"] == 8


def test_five_teams_play_until_champion(logged_in: TestClient, db: Session, user: User) -> None:
    tournament_id = start_tournament(logged_in, db, user, teams=5)

    for round_ in (1, 2, 3):
        for match in bracket(logged_in, tournament_id).values():
            if match["round"] == round_ and match["status"] == "scheduled":
                assert result(logged_in, match["id"], 13, 7).status_code == 200

    page = logged_in.get(f"/tournaments/{tournament_id}").json()
    final = bracket(logged_in, tournament_id)[(3, 1)]
    assert page["status"] == "finished"
    assert final["status"] == "finished"
    assert final["winner_id"] == final["team1_id"]
    assert all(m["status"] == "finished" for m in page["matches"])


def test_tournament_runs_until_final(logged_in: TestClient, db: Session, user: User) -> None:
    tournament_id = start_tournament(logged_in, db, user, teams=4)
    matches = bracket(logged_in, tournament_id)
    result(logged_in, matches[(1, 1)]["id"], 13, 8)

    assert logged_in.get(f"/tournaments/{tournament_id}").json()["status"] == "running"


def test_fix_score_replaces_winner_in_next_match(
    logged_in: TestClient, db: Session, user: User
) -> None:
    tournament_id = start_tournament(logged_in, db, user, teams=4)
    semi = bracket(logged_in, tournament_id)[(1, 1)]
    result(logged_in, semi["id"], 13, 8)

    fixed = result(logged_in, semi["id"], 8, 13)

    assert fixed.status_code == 200
    assert fixed.json()["winner_id"] == semi["team2_id"]
    assert bracket(logged_in, tournament_id)[(2, 1)]["team1_id"] == semi["team2_id"]


def test_cannot_fix_after_next_match_played(logged_in: TestClient, db: Session, user: User) -> None:
    tournament_id = start_tournament(logged_in, db, user, teams=4)
    matches = bracket(logged_in, tournament_id)
    result(logged_in, matches[(1, 1)]["id"], 13, 8)
    result(logged_in, matches[(1, 2)]["id"], 13, 8)
    result(logged_in, matches[(2, 1)]["id"], 13, 8)

    response = result(logged_in, matches[(1, 1)]["id"], 8, 13)

    assert response.status_code == 409
    assert response.json() == {"detail": "Следующий матч уже сыгран"}
    semi = bracket(logged_in, tournament_id)[(1, 1)]
    assert (semi["score1"], semi["score2"]) == (13, 8)  # старый счёт на месте


def test_final_can_be_fixed_after_tournament_finished(
    logged_in: TestClient, db: Session, user: User
) -> None:
    tournament_id = start_tournament(logged_in, db, user, teams=2)
    final = bracket(logged_in, tournament_id)[(1, 1)]
    result(logged_in, final["id"], 13, 8)

    fixed = result(logged_in, final["id"], 8, 13)

    assert fixed.status_code == 200
    assert fixed.json()["winner_id"] == final["team2_id"]
    assert logged_in.get(f"/tournaments/{tournament_id}").json()["status"] == "finished"


def test_match_waiting_for_opponent_is_409(logged_in: TestClient, db: Session, user: User) -> None:
    tournament_id = start_tournament(logged_in, db, user, teams=4)
    final = bracket(logged_in, tournament_id)[(2, 1)]

    response = result(logged_in, final["id"], 13, 8)

    assert response.status_code == 409
    assert response.json() == {"detail": "В матче ещё нет обеих команд"}


def test_bye_match_has_no_score(logged_in: TestClient, db: Session, user: User) -> None:
    tournament_id = start_tournament(logged_in, db, user, teams=3)
    bye = bracket(logged_in, tournament_id)[(1, 1)]
    assert bye["team2_id"] is None

    response = result(logged_in, bye["id"], 13, 0)

    assert response.status_code == 409
    assert response.json() == {"detail": "В матче ещё нет обеих команд"}


@pytest.mark.parametrize(("score1", "score2"), [(13, 13), (-1, 13)])
def test_draw_and_negative_score_are_422(
    logged_in: TestClient, db: Session, user: User, score1: int, score2: int
) -> None:
    tournament_id = start_tournament(logged_in, db, user, teams=2)
    final = bracket(logged_in, tournament_id)[(1, 1)]

    assert result(logged_in, final["id"], score1, score2).status_code == 422
    assert bracket(logged_in, tournament_id)[(1, 1)]["status"] == "scheduled"


def test_only_organizer_sets_result(logged_in: TestClient, db: Session, user: User) -> None:
    tournament_id = start_tournament(logged_in, db, user, teams=2)
    final = bracket(logged_in, tournament_id)[(1, 1)]
    other = User(discord_id="200", nickname="Stranger")
    db.add(other)
    db.commit()
    stranger = TestClient(logged_in.app)
    stranger.cookies.set(ACCESS_TOKEN_COOKIE, create_access_token(other.id))

    response = result(stranger, final["id"], 13, 8)

    assert response.status_code == 403
    assert response.json() == {"detail": "Это может только организатор турнира"}
    assert bracket(logged_in, tournament_id)[(1, 1)]["status"] == "scheduled"


def test_result_requires_login(logged_in: TestClient, db: Session, user: User) -> None:
    tournament_id = start_tournament(logged_in, db, user, teams=2)
    final = bracket(logged_in, tournament_id)[(1, 1)]

    assert result(TestClient(logged_in.app), final["id"], 13, 8).status_code == 401


def test_unknown_match_is_404(logged_in: TestClient) -> None:
    response = result(logged_in, 999, 13, 8)

    assert response.status_code == 404
    assert response.json() == {"detail": "Матч не найден"}
