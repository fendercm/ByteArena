from fastapi import APIRouter
from app.schemas.team import TeamCreate, TeamOut, RegistrationCreate, RegistrationOut

router = APIRouter(prefix="/teams", tags=["teams"])

tournaments_router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@router.post("", response_model=TeamOut, status_code=201)
def create_team(team_in: TeamCreate):
    """
    Создать команду с составом.
    В чате просили возвращать код 201 при создании.
    """
    return TeamOut(
        id=1, 
        name=team_in.name, 
        captain_id=1,
        members=team_in.members
    )


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int):
    """Профиль команды."""
    return TeamOut(
        id=team_id, 
        name="Team Alpha", 
        captain_id=1, 
        members=[1, 2, 3, 4]
    )


@tournaments_router.post("/{tournament_id}/registrations", 
response_model=RegistrationOut, status_code=201)
def register_team_for_tournament(tournament_id: int, reg_in: 
RegistrationCreate):
    """Заявить команду на турнир."""
    return RegistrationOut(
        tournament_id=tournament_id,
        team_id=reg_in.team_id,
        status="pending"
    )

@tournaments_router.patch("/{tournament_id}/registrations/{team_id}", 
response_model=RegistrationOut)
def update_registration_status(tournament_id: int, team_id: int, status: 
str = "approved"):
    """
    Подтвердить или отклонить заявку.
    Статус передается как query-параметр (например, ?status=rejected)
    """
    return RegistrationOut(
        tournament_id=tournament_id,
        team_id=team_id,
        status=status
    )
