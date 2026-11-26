from fastapi import APIRouter, HTTPException, status

from app.auth.dependencies import CurrentUser
from app.db import DbSession
from app.models.match import Match
from app.models.team import Team
from app.routers.organizer import ORGANIZER_ERRORS, tournament_for_organizer
from app.schemas.common import ErrorOut
from app.schemas.match import MatchDetail, MatchOut, MatchResultIn
from app.schemas.team import TeamShort
from app.services.bracket import next_slot

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get(
    "/{match_id}",
    response_model=MatchDetail,
    responses={404: {"model": ErrorOut}},
)
def get_match(match_id: int, db: DbSession) -> MatchDetail:
    """Страница матча."""
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Матч не найден")

    team1 = db.get(Team, match.team1_id) if match.team1_id is not None else None
    team2 = db.get(Team, match.team2_id) if match.team2_id is not None else None

    return MatchDetail.model_validate(
        {
            **{
                name: getattr(match, name)
                for name in MatchDetail.model_fields
                if name not in ("team1", "team2")
            },
            "team1": TeamShort(id=team1.id, name=team1.name) if team1 is not None else None,
            "team2": TeamShort(id=team2.id, name=team2.name) if team2 is not None else None,
        }
    )


@router.post(
    "/{match_id}/result",
    response_model=MatchOut,
    responses={
        **ORGANIZER_ERRORS,
        409: {
            "model": ErrorOut,
            "description": "В матче ещё нет обеих команд или следующий матч уже сыгран",
            "content": {
                "application/json": {
                    "examples": {
                        "teams_missing": {
                            "summary": "Соперник ещё не определён или это проход без игры",
                            "value": {"detail": "В матче ещё нет обеих команд"},
                        },
                        "next_played": {
                            "summary": "Исправлять поздно: следующий матч уже сыгран",
                            "value": {"detail": "Следующий матч уже сыгран"},
                        },
                    }
                }
            },
        },
    },
)
def set_match_result(
    match_id: int, body: MatchResultIn, user: CurrentUser, db: DbSession
) -> MatchOut:
    """Внести или исправить счёт. Победитель — у кого счёт больше; он сразу встаёт
    в следующий матч (при исправлении заменяет прежнего). После финала турнир завершён."""
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Матч не найден")
    # блокируем турнир: два счёта одной сетки сохраняются по очереди
    tournament = tournament_for_organizer(db, match.tournament_id, user, lock=True)
    if match.team1_id is None or match.team2_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="В матче ещё нет обеих команд"
        )

    following = db.get(Match, match.next_match_id) if match.next_match_id else None
    if following is not None and following.status == "finished":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Следующий матч уже сыгран"
        )

    match.score1, match.score2 = body.score1, body.score2
    match.winner_id = match.team1_id if body.score1 > body.score2 else match.team2_id
    match.status = "finished"
    if following is not None:
        slot = next_slot(match.round, match.position)[2]  # нечётная позиция → team1
        setattr(following, slot, match.winner_id)
    else:
        tournament.status = "finished"  # сыгран финал
    db.commit()
    db.refresh(match)
    return MatchOut.model_validate(match)
