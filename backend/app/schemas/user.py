from pydantic import BaseModel


class UserProfileOut(BaseModel):
    id: int
    nickname: str
    avatar_url: str | None = None
