"""Сценарий недели: настоящие HTTP-запросы и отдельная БД, без xfail и подмен маршрутов."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.auth.security import ACCESS_TOKEN_COOKIE, create_access_token
from app.models.match import Match
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
from app.models.user import User


@pytest.fixture
def cup(db, user):
    tournament = Tournament(
        title="Scenario Cup",
        organizer_id=user.id,
        starts_at=datetime.now(UTC) + timedelta(days=1),
        max_teams=8,
        status="closed",
    )
    db.add(tournament)
    db.flush()
    for index in range(4):
        team = Team(name=f"Scenario Team {index}", captain_id=user.id)
        db.add(team)
        db.flush()
        db.add_all(
            [
                TeamMember(team_id=team.id, nickname="Reserve", user_id=None, role="sub"),
                TeamMember(team_id=team.id, nickname="Manual", user_id=None, role="main"),
                TeamMember(
                    team_id=team.id, nickname=user.nickname, user_id=user.id, role="captain"
                ),
            ]
        )
        db.add(TournamentTeam(tournament_id=tournament.id, team_id=team.id, status="approved"))
    db.commit()
    return tournament


def start(client, cup):
    response = client.post(f"/tournaments/{cup.id}/start")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == cup.id
    assert body["status"] == "running"
    return body["matches"]


def result(client, match_id, score1=13, score2=8):
    return client.post(f"/matches/{match_id}/result", json={"score1": score1, "score2": score2})


def snapshot(client, cup):
    response = client.get(f"/tournaments/{cup.id}")
    assert response.status_code == 200
    return response.json()


def test_start_and_play_through_final(logged_in, db, cup):
    matches = start(logged_in, cup)
    assert len(matches) == 3
    first_round = sorted((m for m in matches if m["round"] == 1), key=lambda m: m["position"])
    final = next(m for m in matches if m["round"] == 2)
    approved = set(
        db.scalars(select(TournamentTeam.team_id).where(TournamentTeam.tournament_id == cup.id))
    )
    assert {team_id for m in first_round for team_id in (m["team1_id"], m["team2_id"])} == approved
    assert all(m["next_match_id"] == final["id"] for m in first_round)
    assert final["next_match_id"] is None
    assert final["team1_id"] is None and final["team2_id"] is None

    winners = []
    for match, scores in zip(first_round, [(13, 0), (7, 13)], strict=True):
        response = result(logged_in, match["id"], *scores)
        assert response.status_code == 200, response.text
        body = response.json()
        expected = match["team1_id"] if scores[0] > scores[1] else match["team2_id"]
        assert (body["score1"], body["score2"], body["winner_id"], body["status"]) == (
            *scores,
            expected,
            "finished",
        )
        winners.append(expected)
    before_final = snapshot(logged_in, cup)
    assert before_final["status"] == "running"
    updated_final = next(m for m in before_final["matches"] if m["id"] == final["id"])
    assert (updated_final["team1_id"], updated_final["team2_id"]) == tuple(winners)
    response = result(logged_in, final["id"], 3, 13)
    assert response.status_code == 200, response.text
    assert response.json()["winner_id"] == winners[1]
    finished = snapshot(logged_in, cup)
    assert finished["status"] == "finished"
    assert all(m["status"] == "finished" for m in finished["matches"])
    db.expire_all()
    assert db.get(Match, final["id"]).winner_id == winners[1]
    assert db.get(Tournament, cup.id).status == "finished"


def test_start_requires_organizer(logged_in, db, cup):
    outsider = User(discord_id="scenario-outsider", nickname="Other organizer")
    db.add(outsider)
    db.commit()
    logged_in.cookies.set(ACCESS_TOKEN_COOKIE, create_access_token(outsider.id))
    assert logged_in.post(f"/tournaments/{cup.id}/start").status_code == 403
    assert snapshot(logged_in, cup)["matches"] == []
    db.expire_all()
    assert db.get(Tournament, cup.id).status == "closed"


def test_result_requires_organizer(logged_in, db, cup):
    match = next(m for m in start(logged_in, cup) if m["round"] == 1)
    before = snapshot(logged_in, cup)
    outsider = User(discord_id="scenario-player", nickname="Other player")
    db.add(outsider)
    db.commit()
    logged_in.cookies.set(ACCESS_TOKEN_COOKIE, create_access_token(outsider.id))
    assert result(logged_in, match["id"]).status_code == 403
    assert snapshot(logged_in, cup) == before


@pytest.mark.parametrize("scores", [(13, 13), (0, 0), (-1, 13)])
def test_invalid_result_does_not_change_bracket(logged_in, cup, scores):
    match = next(m for m in start(logged_in, cup) if m["round"] == 1)
    before = snapshot(logged_in, cup)
    assert result(logged_in, match["id"], *scores).status_code == 422
    assert snapshot(logged_in, cup) == before


@pytest.mark.parametrize("position,slot", [(1, "team1_id"), (2, "team2_id")])
def test_score_correction_replaces_winner_before_next_match(logged_in, cup, position, slot):
    matches = start(logged_in, cup)
    match = next(m for m in matches if m["round"] == 1 and m["position"] == position)
    final_id = match["next_match_id"]
    assert result(logged_in, match["id"], 13, 8).status_code == 200
    before = snapshot(logged_in, cup)
    final = next(m for m in before["matches"] if m["id"] == final_id)
    assert final[slot] == match["team1_id"]
    response = result(logged_in, match["id"], 0, 13)
    assert response.status_code == 200, response.text
    assert response.json()["winner_id"] == match["team2_id"]
    after = snapshot(logged_in, cup)
    corrected = next(m for m in after["matches"] if m["id"] == match["id"])
    assert (corrected["score1"], corrected["score2"]) == (0, 13)
    updated_final = next(m for m in after["matches"] if m["id"] == final_id)
    assert updated_final == {**final, slot: match["team2_id"]}
    assert after["status"] == "running"


@pytest.mark.parametrize("scores", [(0, 13), (13, 7)])
def test_score_correction_rejected_after_next_match(logged_in, cup, scores):
    matches = start(logged_in, cup)
    semis = sorted((m for m in matches if m["round"] == 1), key=lambda m: m["position"])
    for match in semis:
        assert result(logged_in, match["id"]).status_code == 200
    final_id = semis[0]["next_match_id"]
    assert result(logged_in, final_id).status_code == 200
    before = snapshot(logged_in, cup)
    response = result(logged_in, semis[0]["id"], *scores)
    assert response.status_code == 409, response.text
    assert snapshot(logged_in, cup) == before


def test_unknown_match_returns_404(client):
    response = client.get("/matches/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Матч не найден"


def test_match_detail_uses_saved_teams_and_result(logged_in, db, cup, user):
    match = next(m for m in start(logged_in, cup) if m["round"] == 1)
    assert result(logged_in, match["id"], 0, 13).status_code == 200
    response = logged_in.get(f"/matches/{match['id']}")
    assert response.status_code == 200
    body = response.json()
    assert (body["id"], body["tournament_id"], body["score1"], body["score2"]) == (
        match["id"],
        cup.id,
        0,
        13,
    )
    for slot in ("team1", "team2"):
        team = db.get(Team, match[f"{slot}_id"])
        assert body[slot] == {
            "id": team.id,
            "name": team.name,
            "captain_id": user.id,
            "members": [
                {"nickname": user.nickname, "user_id": user.id, "role": "captain"},
                {"nickname": "Manual", "user_id": None, "role": "main"},
                {"nickname": "Reserve", "user_id": None, "role": "sub"},
            ],
        }
    assert body["winner_id"] == match["team2_id"]
    assert body["status"] == "finished"
