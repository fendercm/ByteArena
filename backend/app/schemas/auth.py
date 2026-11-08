from pydantic import BaseModel, ConfigDict


class UserMeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str
    avatar_url: str | None = None
