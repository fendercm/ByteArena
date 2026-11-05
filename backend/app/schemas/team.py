from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

TeamMemberRole = Literal["captain", "main", "sub"]
RegistrationStatus = Literal["pending", "approved", "rejected"]


class TeamShort(BaseModel):
    """Команда в чужом ответе: в сетке, на странице матча или турнира."""

    id: int
    name: str


class TeamMemberCreate(BaseModel):
    user_id: int
    role: TeamMemberRole


class TeamMemberOut(TeamMemberCreate):
    nickname: str
    avatar_url: str | None = None


class TeamCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=64)
    members: list[TeamMemberCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_members(self) -> Self:
        member_ids = [member.user_id for member in self.members]
        if len(member_ids) != len(set(member_ids)):
            raise ValueError("Игрок не может повторяться в составе команды")
        if sum(member.role == "captain" for member in self.members) != 1:
            raise ValueError("В составе должен быть ровно один капитан")
        return self


class TeamOut(TeamShort):
    captain_id: int
    members: list[TeamMemberOut]


class RegistrationCreate(BaseModel):
    team_id: int


class RegistrationUpdate(BaseModel):
    status: Literal["approved", "rejected"]


class RegistrationOut(BaseModel):
    tournament_id: int
    team_id: int
    status: RegistrationStatus
