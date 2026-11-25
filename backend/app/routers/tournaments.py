from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import ColumnElement, ScalarSelect, func, select

from app.auth.dependencies import CurrentUser
from app.db import DbSession
from app.models.match import Match
from app.models.team import Team
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
from app.routers.organizer import ORGANIZER_ERRORS, tournament_for_organizer
from app.schemas.common import ErrorOut
from app.schemas.match import MatchOut
from app.schemas.tournament import (
    TournamentCreate,
    TournamentDetail,
    TournamentList,
    TournamentOut,
    TournamentStatus,
    TournamentTeamOut,
)
from app.services.bracket import BracketError, save_bracket

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


def _teams_count(tournament_id: ColumnElement[int]) -> ScalarSelect[int]:
    """Подзапрос: сколько заявок турнира одобрено. Считается в базе, а не хранится."""
    return (
        select(func.count())
        .where(
            TournamentTeam.tournament_id == tournament_id,
            TournamentTeam.status == "approved",
        )
        .scalar_subquery()
    )


def _out(tournament: Tournament, teams_count: int) -> TournamentOut:
    return TournamentOut.model_validate(
        {
            **{
                name: getattr(tournament, name)
                for name in TournamentOut.model_fields
                if name != "teams_count"
            },
            "teams_count": teams_count,
        }
    )


@router.get("", response_model=TournamentList)
def list_tournaments(
    db: DbSession,
    status_: Annotated[
        list[TournamentStatus] | None,
        Query(alias="status", description="Только эти статусы, например ?status=running"),
    ] = None,
) -> TournamentList:
    """Список турниров для главной: ближайшие сначала."""
    query = select(Tournament, _teams_count(Tournament.id)).order_by(
        Tournament.starts_at, Tournament.id
    )
    if status_:
        query = query.where(Tournament.status.in_(status_))
    items = [_out(tournament, count) for tournament, count in db.execute(query)]
    return TournamentList(items=items, total=len(items))


@router.post(
    "",
    response_model=TournamentOut,
    status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ErrorOut}},
)
def create_tournament(body: TournamentCreate, user: CurrentUser, db: DbSession) -> TournamentOut:
    """Создать турнир. Организатор — тот, кто вошёл. Регистрация команд открывается сразу."""
    # статус registration, а не draft: новый турнир сразу виден на главной в «Ближайших»
    tournament = Tournament(**body.model_dump(), organizer_id=user.id, status="registration")
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    return _out(tournament, teams_count=0)


@router.get(
    "/{tournament_id}",
    response_model=TournamentDetail,
    responses={404: {"model": ErrorOut}},
)
def get_tournament(tournament_id: int, db: DbSession) -> TournamentDetail:
    """Страница турнира: данные, команды с заявками и сетка (до старта пустая)."""
    row = db.execute(
        select(Tournament, _teams_count(Tournament.id)).where(Tournament.id == tournament_id)
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Турнир не найден")
    tournament, teams_count = row

    teams = db.execute(
        select(Team.id, Team.name, TournamentTeam.status)
        .join(TournamentTeam, TournamentTeam.team_id == Team.id)
        .where(TournamentTeam.tournament_id == tournament_id)
        .order_by(Team.name)
    )
    matches = db.scalars(
        select(Match)
        .where(Match.tournament_id == tournament_id)
        .order_by(Match.round, Match.position)
    )
    return TournamentDetail(
        **_out(tournament, teams_count).model_dump(),
        teams=[TournamentTeamOut(id=id_, name=name, status=st) for id_, name, st in teams],
        matches=[MatchOut.model_validate(match) for match in matches],
    )


@router.post(
    "/{tournament_id}/start",
    response_model=TournamentDetail,
    responses={
        **ORGANIZER_ERRORS,
        409: {
            "model": ErrorOut,
            "description": "Регистрация ещё не закрыта или турнир уже запущен",
            "content": {
                "application/json": {
                    "examples": {
                        "not_closed": {
                            "summary": "Регистрация ещё открыта",
                            "value": {"detail": "Регистрация ещё не закрыта"},
                        },
                        "already_started": {
                            "summary": "Турнир уже запущен или завершён",
                            "value": {"detail": "Турнир уже запущен"},
                        },
                    }
                }
            },
        },
    },
)
def start_tournament(tournament_id: int, user: CurrentUser, db: DbSession) -> TournamentDetail:
    """Запустить турнир: closed → running, сетка строится из подтверждённых команд.
    Проходы без игры сохраняются сыгранными, их победители уже стоят во втором раунде."""
    tournament = tournament_for_organizer(db, tournament_id, user, lock=True)
    if tournament.status in ("running", "finished"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Турнир уже запущен")
    if tournament.status != "closed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Регистрация ещё не закрыта"
        )

    try:
        save_bracket(db, tournament)
    except BracketError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    tournament.status = "running"
    db.commit()  # сетка и смена статуса — одна транзакция: либо обе, либо ничего
    return get_tournament(tournament_id, db)
