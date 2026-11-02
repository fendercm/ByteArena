from pydantic import BaseModel

class UserProfileOut(BaseModel):
    id: int
    username: str
    rating: int
    games_played: int
