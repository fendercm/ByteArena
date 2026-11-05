from pydantic import BaseModel


class UserMeOut(BaseModel):
    id: int
    nickname: str
    avatar_url: str | None = None
