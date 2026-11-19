from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TeamMemberRole = Literal["captain", "main", "sub"]
RegistrationStatus = Literal["pending", "approved", "rejected"]


class TeamShort(BaseModel):
    """Команда в чужом ответе: в сетке, на странице матча или турнира."""

    id: int
    name: str


class MemberIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nickname: str = Field(min_length=2, max_length=32)
    user_id: int | None = None
    role: Literal["main", "sub"]


class TeamMemberOut(BaseModel):
    nickname: str
    user_id: int | None
    role: TeamMemberRole


class TeamCreate(BaseModel):
    """Данные для создания команды и её состава."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=32)
    members: list[MemberIn] = Field(
        description="Участники команды: четыре основных и до двух запасных."
    )

    @model_validator(mode="after")
    def check_roster(self):
        main = [member for member in self.members if member.role == "main"]
        subs = [member for member in self.members if member.role == "sub"]
        if len(main) != 4:
            raise ValueError("В основном составе капитан и ещё 4 игрока")
        if len(subs) > 2:
            raise ValueError("Запасных — не больше двух")
        nicknames = [member.nickname.lower() for member in self.members]
        if len(nicknames) != len(set(nicknames)):
            raise ValueError("Ники в составе повторяются")
        return self


class TeamOut(TeamShort):
    captain_id: int
    members: list[TeamMemberOut]


class TournamentTeamsOut(BaseModel):
    items: list[TeamOut]
    total: int


class RegistrationCreate(BaseModel):
    team_id: int


class RegistrationUpdate(BaseModel):
    status: Literal["approved", "rejected"]


class RegistrationOut(BaseModel):
    id: int
    tournament_id: int
    team_id: int
    status: RegistrationStatus
