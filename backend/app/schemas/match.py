from typing import Literal, Self

from pydantic import AwareDatetime, BaseModel, Field, model_validator

from app.schemas.team import TeamShort

MatchStatus = Literal["scheduled", "live", "finished"]


class MatchOut(BaseModel):
    """Матч в сетке турнира."""

    id: int
    tournament_id: int
    round: int  # 1 = первый раунд
    position: int  # номер матча внутри раунда, с 1
    team1_id: int | None
    team2_id: int | None
    score1: int | None
    score2: int | None
    winner_id: int | None
    status: MatchStatus
    scheduled_at: AwareDatetime | None
    next_match_id: int | None  # куда уходит победитель; у финала null


class MatchDetail(MatchOut):
    """Страница матча: к данным сетки добавлены названия команд."""

    team1: TeamShort | None
    team2: TeamShort | None


class MatchResultIn(BaseModel):
    """Счёт от организатора. Победителя бэкенд определяет сам: у кого счёт больше."""

    score1: int = Field(ge=0)
    score2: int = Field(ge=0)

    @model_validator(mode="after")
    def no_draw(self) -> Self:
        if self.score1 == self.score2:
            raise ValueError("Ничьей быть не может: в сетке нужен победитель")
        return self
