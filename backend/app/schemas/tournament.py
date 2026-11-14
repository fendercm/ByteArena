from datetime import UTC, datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import UtcDatetime
from app.schemas.match import MatchOut
from app.schemas.team import TeamShort

TournamentStatus = Literal["draft", "registration", "closed", "running", "finished"]
RegistrationStatus = Literal["pending", "approved", "rejected"]


class TournamentCreate(BaseModel):
    """Форма создания турнира. id, status и organizer_id задаёт сервер."""

    # пробелы по краям обрезаются до проверки длины: название из одних пробелов не пройдёт
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=128)
    description: str | None = None
    game: Literal["cs2"] = "cs2"
    starts_at: AwareDatetime
    # сетка на выбывание делится пополам без пропусков раунда только при 4, 8 и 16 командах
    max_teams: Literal[4, 8, 16]
    rules: str | None = None

    @field_validator("starts_at")
    @classmethod
    def not_in_past(cls, value: datetime) -> datetime:
        if value < datetime.now(UTC):
            raise ValueError("Дата турнира не может быть в прошлом")
        return value


class TournamentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    game: str
    starts_at: UtcDatetime
    max_teams: int
    teams_count: int  # сколько заявок одобрено; для карточки на главной
    rules: str | None
    status: TournamentStatus
    organizer_id: int
    created_at: UtcDatetime


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
