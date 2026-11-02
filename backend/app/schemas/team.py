from pydantic import BaseModel


class TeamShort(BaseModel):
    """Команда в чужом ответе: в сетке, на странице матча или турнира."""

    id: int
    name: str
