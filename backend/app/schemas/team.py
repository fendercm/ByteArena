from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

TeamMemberRole = Literal["captain", "main", "sub"]
TeamInputRole = Literal["main", "sub"]
RegistrationStatus = Literal["pending", "approved", "rejected"]


class TeamShort(BaseModel):
    """Команда в чужом ответе: в сетке, на странице матча или турнира."""

    id: int
    name: str


class MemberIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nickname: str = Field(min_length=2, max_length=32)
    user_id: int | None = None
    role: TeamInputRole


class TeamMemberOut(BaseModel):
    nickname: str
    user_id: int | None
    role: TeamMemberRole


class TeamCreate(BaseModel):
    """Команда с четырьмя основными игроками и максимум двумя запасными."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=32)
    members: list[MemberIn] = Field(
        min_length=4,
        max_length=6,
        description=(
            "Ровно 4 участника с ролью main и не более 2 с ролью sub; "
            "ники должны быть уникальны без учёта регистра."
        ),
    )

    @model_validator(mode="after")
    def validate_members(self) -> Self:
        if sum(member.role == "main" for member in self.members) != 4:
            raise ValueError("В составе должно быть ровно 4 основных игрока")
        if sum(member.role == "sub" for member in self.members) > 2:
            raise ValueError("В составе может быть не более 2 запасных игроков")
        nicknames = [member.nickname.casefold() for member in self.members]
        if len(nicknames) != len(set(nicknames)):
            raise ValueError("Ники в составе не должны повторяться")
        return self


class TeamOut(TeamShort):
    captain_id: int
    members: list[TeamMemberOut]


class RegistrationCreate(BaseModel):
    team_id: int


class RegistrationUpdate(BaseModel):
    status: Literal["approved", "rejected"]


class RegistrationOut(BaseModel):
    id: int
    tournament_id: int
    team_id: int
    status: RegistrationStatus
