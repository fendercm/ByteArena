from pydantic import BaseModel, ConfigDict

from app.schemas.team import TeamShort


class UserMeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str
    avatar_url: str | None = None
    team: TeamShort | None = None
