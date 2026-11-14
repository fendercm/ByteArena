from typing import Literal

from pydantic import BaseModel

from app.schemas.team import RegistrationStatus, TeamShort


class RegistrationMemberOut(BaseModel):
    """Место в составе: user_id есть у зарегистрированного игрока, у ника без аккаунта — null."""

    nickname: str
    user_id: int | None
    role: Literal["captain", "main", "sub"]


class RegistrationAdminOut(BaseModel):
    """Заявка в панели организатора: команда, её состав и статус."""

    id: int
    tournament_id: int
    team: TeamShort
    status: RegistrationStatus
    members: list[RegistrationMemberOut]


class RegistrationAdminList(BaseModel):
    items: list[RegistrationAdminOut]
    total: int
