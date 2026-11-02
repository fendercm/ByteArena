from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

from app.schemas.match import MatchOut
from app.schemas.team import TeamShort

TournamentStatus = Literal["draft", "registration", "running", "finished"]
RegistrationStatus = Literal["pending", "approved", "rejected"]


class TournamentCreate(BaseModel):
    """Форма создания турнира. id, status и organizer_id задаёт сервер."""

    title: str = Field(min_length=1, max_length=128)
    description: str | None = None
    game: Literal["cs2"] = "cs2"
    starts_at: AwareDatetime
    max_teams: int = Field(ge=2)
    rules: str | None = None


class TournamentOut(BaseModel):
    id: int
    title: str
    description: str | None
    game: str
    starts_at: AwareDatetime
    max_teams: int
    teams_count: int  # сколько заявок одобрено; для карточки на главной
    rules: str | None
    status: TournamentStatus
    organizer_id: int
    created_at: AwareDatetime


class TournamentList(BaseModel):
    items: list[TournamentOut]
    total: int


class TournamentTeamOut(TeamShort):
    """Команда на странице турнира вместе со статусом её заявки."""

    status: RegistrationStatus


class TournamentDetail(TournamentOut):
    """Страница турнира: данные, команды и сетка. До старта matches пустой."""

    teams: list[TournamentTeamOut]
    matches: list[MatchOut]
