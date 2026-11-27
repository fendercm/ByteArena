from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.tournament import Tournament

TournamentResultStatus = Literal["champion", "eliminated", "running"]


@dataclass(frozen=True)
class TournamentResult:
    result: TournamentResultStatus | None
    eliminated_round: int | None = None


def get_tournament_result(db: Session, tournament: Tournament, team_id: int) -> TournamentResult:
    """Return a team's outcome based on its completed matches in a tournament."""
    matches = db.scalars(
        select(Match)
        .where(
            Match.tournament_id == tournament.id,
            (Match.team1_id == team_id) | (Match.team2_id == team_id),
        )
        .order_by(Match.round, Match.position)
    ).all()

    losses = [
        match for match in matches
        if match.status == "finished" and match.winner_id is not None and match.winner_id != team_id
    ]
    if losses:
        return TournamentResult("eliminated", min(match.round for match in losses))

    if tournament.status == "finished":
        final = db.scalar(
            select(Match)
            .where(Match.tournament_id == tournament.id)
            .order_by(Match.round.desc(), Match.position)
            .limit(1)
        )
        if final is not None and final.status == "finished" and final.winner_id == team_id:
            return TournamentResult("champion")
        if matches:
            return TournamentResult("eliminated", None)
        return TournamentResult(None)

    if tournament.status == "running":
        return TournamentResult("running")

    return TournamentResult(None)
