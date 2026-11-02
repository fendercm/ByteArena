from pydantic import BaseModel
from typing import List

class TeamShort(BaseModel):
    id: int
    name: str


class TeamCreate(BaseModel):
    name: str
    members: List[int]

class TeamOut(TeamShort):
    captain_id: int
    members: List[int]

class RegistrationCreate(BaseModel):
    team_id: int

class RegistrationOut(BaseModel):
    tournament_id: int
    team_id: int
    status: str