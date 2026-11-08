from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import ColumnElement, ScalarSelect, func, select

from app.auth.dependencies import CurrentUser
from app.db import DbSession
from app.models.match import Match
from app.models.team import Team
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
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

router = APIRouter(prefix="/tournaments", tags=["tournaments"])

# Пример для заглушки POST /{id}/start: настоящий запуск и сетка появятся позже
EXAMPLE = TournamentOut(
    id=1,
    title="Autumn Championship 2026",
    description="Сезонный турнир по Counter-Strike",
    game="cs2",
    starts_at=datetime.fromisoformat("2026-11-05T18:00:00+03:00"),
    max_teams=4,
    teams_count=4,
    rules="Single elimination, best of three",
    status="registration",
    organizer_id=1,
    created_at=datetime.fromisoformat("2026-10-25T12:00:00+03:00"),
)

EXAMPLE_TEAMS = [
    TournamentTeamOut(id=1, name="Night Wolves", status="approved"),
    TournamentTeamOut(id=2, name="Frostbyte", status="approved"),
    TournamentTeamOut(id=3, name="Red Phoenix", status="approved"),
    TournamentTeamOut(id=4, name="Shadow Protocol", status="approved"),
]


def example_detail(tournament_id: int) -> TournamentDetail:
    """Идущий турнир на 4 команды: первый полуфинал сыгран, его победитель уже в финале."""
    return TournamentDetail(
        **EXAMPLE.model_dump(exclude={"id", "status"}),
        id=tournament_id,
        status="running",
        teams=EXAMPLE_TEAMS,
        matches=[
            MatchOut(
                id=1,
                tournament_id=tournament_id,
                round=1,
                position=1,
                team1_id=1,
                team2_id=2,
                score1=13,
                score2=8,
                winner_id=1,
                status="finished",
                scheduled_at=datetime.fromisoformat("2026-11-05T18:00:00+03:00"),
                next_match_id=3,
            ),
            MatchOut(
                id=2,
                tournament_id=tournament_id,
                round=1,
                position=2,
                team1_id=3,
                team2_id=4,
                score1=None,
                score2=None,
                winner_id=None,
                status="scheduled",
                scheduled_at=datetime.fromisoformat("2026-11-05T19:00:00+03:00"),
                next_match_id=3,
            ),
            MatchOut(
                id=3,
                tournament_id=tournament_id,
                round=2,
                position=1,
                team1_id=1,
                team2_id=None,
                score1=None,
                score2=None,
                winner_id=None,
                status="scheduled",
                scheduled_at=None,
                next_match_id=None,
            ),
        ],
    )


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
        401: {"model": ErrorOut},
        403: {"model": ErrorOut},
        404: {"model": ErrorOut},
        409: {"model": ErrorOut},
    },
)
def start_tournament(tournament_id: int) -> TournamentDetail:
    """Запустить турнир и построить сетку. 409: уже запущен или мало команд."""
    # ЗАГЛУШКА: логика появится на неделе 3
    return example_detail(tournament_id)
