from pydantic import BaseModel

class UserMeOut(BaseModel):
    id: int
    username: str
    avatar_url: str | None = None
