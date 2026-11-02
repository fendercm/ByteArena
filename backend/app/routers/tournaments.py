from datetime import datetime

from fastapi import APIRouter

from app.schemas.common import ErrorOut
from app.schemas.match import MatchOut
from app.schemas.tournament import (
    TournamentCreate,
    TournamentDetail,
    TournamentList,
    TournamentOut,
    TournamentTeamOut,
)

router = APIRouter(prefix="/tournaments", tags=["tournaments"])

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


@router.get("", response_model=TournamentList)
def list_tournaments() -> TournamentList:
    """Список турниров для главной."""
    # ЗАГЛУШКА: логика появится на неделе 3
    return TournamentList(items=[EXAMPLE], total=1)


@router.post(
    "",
    response_model=TournamentOut,
    status_code=201,
    responses={401: {"model": ErrorOut}},
)
def create_tournament(body: TournamentCreate) -> TournamentOut:
    """Создать турнир. Организатором становится текущий пользователь."""
    # ЗАГЛУШКА: логика появится на неделе 3
    return TournamentOut(
        **body.model_dump(),
        id=1,
        teams_count=0,
        status="draft",
        organizer_id=1,
        created_at=datetime.fromisoformat("2026-10-25T12:00:00+03:00"),
    )


@router.get(
    "/{tournament_id}",
    response_model=TournamentDetail,
    responses={404: {"model": ErrorOut}},
)
def get_tournament(tournament_id: int) -> TournamentDetail:
    """Страница турнира: данные, команды и сетка."""
    # ЗАГЛУШКА: логика появится на неделе 3
    return example_detail(tournament_id)


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
