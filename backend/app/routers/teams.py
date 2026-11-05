from fastapi import APIRouter

from app.schemas.common import ErrorOut
from app.schemas.team import (
    RegistrationCreate,
    RegistrationOut,
    RegistrationUpdate,
    TeamCreate,
    TeamMemberOut,
    TeamOut,
)

router = APIRouter(prefix="/teams", tags=["teams"])

tournaments_router = APIRouter(prefix="/tournaments", tags=["tournaments"])


def _member_profile(user_id: int, role: str) -> TeamMemberOut:
    return TeamMemberOut(
        user_id=user_id,
        role=role,
        nickname=f"Player{user_id}",
        avatar_url=f"https://example.com/avatars/{user_id}.png",
    )


@router.post(
    "",
    response_model=TeamOut,
    status_code=201,
    responses={401: {"model": ErrorOut}},
)
def create_team(team_in: TeamCreate):
    """
    Создать команду с составом.
    """
    return TeamOut(
        id=1,
        name=team_in.name,
        captain_id=next(member.user_id for member in team_in.members if member.role == "captain"),
        members=[_member_profile(member.user_id, member.role) for member in team_in.members],
    )


@router.get("/{team_id}", response_model=TeamOut, responses={404: {"model": ErrorOut}})
def get_team(team_id: int):
    """Профиль команды."""
    return TeamOut(
        id=team_id,
        name="Team Alpha",
        captain_id=1,
        members=[
            _member_profile(1, "captain"),
            _member_profile(2, "main"),
            _member_profile(3, "main"),
            _member_profile(4, "sub"),
        ],
    )


@tournaments_router.post(
    "/{tournament_id}/registrations",
    response_model=RegistrationOut,
    status_code=201,
    responses={401: {"model": ErrorOut}, 404: {"model": ErrorOut}},
)
def register_team_for_tournament(tournament_id: int, reg_in: RegistrationCreate):
    """Заявить команду на турнир."""
    return RegistrationOut(tournament_id=tournament_id, team_id=reg_in.team_id, status="pending")


@tournaments_router.patch(
    "/{tournament_id}/registrations/{team_id}",
    response_model=RegistrationOut,
    responses={
        401: {"model": ErrorOut},
        403: {"model": ErrorOut},
        404: {"model": ErrorOut},
    },
)
def update_registration_status(
    tournament_id: int, team_id: int, registration_in: RegistrationUpdate
):
    """
    Подтвердить или отклонить заявку.
    Статус передается в теле запроса.
    """
    return RegistrationOut(
        tournament_id=tournament_id,
        team_id=team_id,
        status=registration_in.status,
    )
