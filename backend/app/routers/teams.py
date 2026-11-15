from fastapi import APIRouter, Header, HTTPException, status

from app.schemas.common import ErrorOut
from app.schemas.team import (
    RegistrationCreate,
    RegistrationOut,
    TeamCreate,
    TeamMemberOut,
    TeamOut,
)

router = APIRouter(prefix="/teams", tags=["teams"])

tournaments_router = APIRouter(prefix="/tournaments", tags=["tournaments"])


def _fake_team(team_id: int, name: str, captain_id: int) -> TeamOut:
    return TeamOut(
        id=team_id,
        name=name,
        captain_id=captain_id,
        members=[
            TeamMemberOut(nickname="Fedor", user_id=captain_id, role="captain"),
            TeamMemberOut(nickname="Ali", user_id=2, role="main"),
            TeamMemberOut(nickname="Mira", user_id=None, role="main"),
            TeamMemberOut(nickname="Nova", user_id=4, role="main"),
            TeamMemberOut(nickname="Ghost", user_id=None, role="main"),
        ],
    )


def _require_fake_user(user_id: int | None) -> int:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сначала войдите через Discord",
        )
    return user_id


@router.post(
    "",
    response_model=TeamOut,
    status_code=201,
    summary="Создать команду",
    description="Создаёт mock-команду; X-User-Id задаёт текущего пользователя-капитана.",
    responses={401: {"model": ErrorOut, "description": "Сначала войдите через Discord"}},
)
def create_team(
    team_in: TeamCreate,
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> TeamOut:
    """Вернуть переданный состав с фиктивным ID команды."""
    captain_id = _require_fake_user(x_user_id)
    return TeamOut(
        id=1,
        name=team_in.name,
        captain_id=captain_id,
        members=[TeamMemberOut(nickname="Fedor", user_id=captain_id, role="captain")]
        + [member.model_dump() for member in team_in.members],
    )


@router.get(
    "/{id}",
    response_model=TeamOut,
    summary="Получить команду",
    description="Возвращает mock-профиль команды и её состав.",
)
def get_team(id: int) -> TeamOut:
    """Профиль команды с участниками, в том числе без аккаунтов."""
    return _fake_team(id, "Night Wolves", captain_id=1)


@tournaments_router.get(
    "/{id}/teams",
    response_model=list[TeamOut],
    summary="Команды турнира",
    description="Возвращает mock-список команд, участвующих в турнире.",
)
def list_tournament_teams(id: int) -> list[TeamOut]:
    """Фиктивные команды турнира."""
    return [
        _fake_team(1, "Night Wolves", captain_id=1),
        _fake_team(2, "Frostbyte", captain_id=5),
        _fake_team(3, "Red Phoenix", captain_id=8),
    ]


@tournaments_router.post(
    "/{tournament_id}/registrations",
    response_model=RegistrationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Подать заявку на турнир",
    description="Создаёт mock-заявку команды со статусом pending.",
    responses={
        401: {"model": ErrorOut, "description": "Сначала войдите через Discord"},
        403: {
            "model": ErrorOut,
            "description": "Нельзя подать заявку от имени этой команды",
            "content": {
                "application/json": {
                    "example": {"detail": "Нельзя подать заявку от имени этой команды"}
                }
            },
        },
        409: {
            "model": ErrorOut,
            "description": "Команда уже зарегистрирована или регистрация закрыта",
            "content": {
                "application/json": {
                    "example": {"detail": "Команда уже зарегистрирована или регистрация закрыта"}
                }
            },
        },
    },
)
def register_team_for_tournament(
    tournament_id: int,
    reg_in: RegistrationCreate,
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> RegistrationOut:
    """Вернуть фиктивную заявку; без X-User-Id возвращает 401."""
    _require_fake_user(x_user_id)
    return RegistrationOut(
        id=1, tournament_id=tournament_id, team_id=reg_in.team_id, status="pending"
    )


@tournaments_router.get(
    "/{id}/my-registration",
    response_model=RegistrationOut,
    summary="Моя заявка на турнир",
    description="Возвращает mock-заявку текущего пользователя со статусом approved.",
    responses={401: {"model": ErrorOut, "description": "Сначала войдите через Discord"}},
)
def get_my_registration(
    id: int,
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> RegistrationOut:
    """Вернуть фиктивный статус заявки вошедшего пользователя."""
    user_id = _require_fake_user(x_user_id)
    return RegistrationOut(id=1, tournament_id=id, team_id=user_id, status="approved")
