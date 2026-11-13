from pydantic import BaseModel, Field

from app.schemas.team import TeamShort


class TournamentProfileOut(BaseModel):
    id: int
    title: str


class UserProfileOut(BaseModel):
    id: int
    nickname: str
    avatar_url: str | None = None
    team: TeamShort | None = None
    tournaments: list[TournamentProfileOut] = Field(default_factory=list)
