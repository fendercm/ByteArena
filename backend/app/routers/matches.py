from datetime import datetime

from fastapi import APIRouter

from app.schemas.common import ErrorOut
from app.schemas.match import MatchDetail, MatchOut, MatchResultIn
from app.schemas.team import TeamShort

router = APIRouter(prefix="/matches", tags=["matches"])

EXAMPLE = MatchOut(
    id=1,
    tournament_id=1,
    round=1,
    position=1,
    team1_id=1,
    team2_id=2,
    score1=None,
    score2=None,
    winner_id=None,
    status="scheduled",
    scheduled_at=datetime.fromisoformat("2026-11-05T18:00:00+03:00"),
    next_match_id=3,
)


@router.get(
    "/{match_id}",
    response_model=MatchDetail,
    responses={404: {"model": ErrorOut}},
)
def get_match(match_id: int) -> MatchDetail:
    """Страница матча."""
    # ЗАГЛУШКА: логика появится на неделе 3
    return MatchDetail(
        **EXAMPLE.model_dump(exclude={"id"}),
        id=match_id,
        team1=TeamShort(id=1, name="Night Wolves"),
        team2=TeamShort(id=2, name="Frostbyte"),
    )


@router.post(
    "/{match_id}/result",
    response_model=MatchOut,
    responses={
        401: {"model": ErrorOut},
        403: {"model": ErrorOut},
        404: {"model": ErrorOut},
        409: {"model": ErrorOut},
    },
)
def set_match_result(match_id: int, body: MatchResultIn) -> MatchOut:
    """Внести или исправить счёт. Победитель уходит в следующий матч."""
    # ЗАГЛУШКА: логика появится на неделе 3
    return MatchOut(
        **EXAMPLE.model_dump(exclude={"id", "score1", "score2", "winner_id", "status"}),
        id=match_id,
        score1=body.score1,
        score2=body.score2,
        winner_id=EXAMPLE.team1_id if body.score1 > body.score2 else EXAMPLE.team2_id,
        status="finished",
    )
