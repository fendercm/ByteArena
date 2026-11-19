from fastapi import APIRouter, HTTPException, status

from app.auth.dependencies import CurrentUser
from app.db import DbSession
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.common import ErrorOut
from app.schemas.team import (
    RegistrationCreate,
    RegistrationOut,
    TeamCreate,
    TeamMemberOut,
    TeamOut,
    TournamentTeamsOut,
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


@router.post(
    "",
    response_model=TeamOut,
    status_code=201,
    summary="Создать команду",
    description="Создаёт команду; капитаном становится вошедший пользователь.",
    responses={
        400: {
            "model": ErrorOut,
            "description": "Ник капитана повторяется или игрок указан несколько раз",
            "content": {
                "application/json": {
                    "examples": {
                        "captain_nickname_duplicate": {
                            "summary": "Ник капитана повторяется",
                            "value": {"detail": "Ник капитана не должен повторяться в составе"},
                        },
                        "player_duplicate": {
                            "summary": "Игрок указан несколько раз",
                            "value": {"detail": "Игрок указан в составе несколько раз"},
                        },
                    }
                }
            },
        },
        401: {"model": ErrorOut, "description": "Сначала войдите через Discord"},
        404: {"model": ErrorOut, "description": "Указанный игрок не найден"},
    },
)
def create_team(team_in: TeamCreate, user: CurrentUser, db: DbSession) -> TeamOut:
    """Сохранить команду и состав; ник зарегистрированного игрока брать из его профиля."""
    captain_nickname = user.nickname.casefold()
    seen_nicknames: set[str] = set()
    members: list[TeamMember] = []

    for member in team_in.members:
        member_user = db.get(User, member.user_id) if member.user_id is not None else None
        if member.user_id is not None and member_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Игрок с ID {member.user_id} не найден",
            )

        nickname = member_user.nickname if member_user is not None else member.nickname
        normalized_nickname = nickname.casefold()
        if normalized_nickname == captain_nickname:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ник капитана не должен повторяться в составе",
            )
        if normalized_nickname in seen_nicknames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Игрок указан в составе несколько раз",
            )
        if len(nickname) > 32:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ник участника не должен быть длиннее 32 символов",
            )

        seen_nicknames.add(normalized_nickname)
        members.append(
            TeamMember(
                user_id=member.user_id,
                nickname=nickname,
                role=member.role,
            )
        )

    team = Team(name=team_in.name, captain_id=user.id)
    db.add(team)
    db.flush()

    captain = TeamMember(
        team_id=team.id,
        user_id=user.id,
        nickname=user.nickname,
        role="captain",
    )
    for member in members:
        member.team_id = team.id
    db.add_all([captain, *members])
    db.commit()
    db.refresh(team)

    return TeamOut(
        id=team.id,
        name=team.name,
        captain_id=team.captain_id,
        members=[
            TeamMemberOut(nickname=captain.nickname, user_id=captain.user_id, role=captain.role),
            *[
                TeamMemberOut(nickname=member.nickname, user_id=member.user_id, role=member.role)
                for member in members
            ],
        ],
    )


@router.get(
    "/{team_id}",
    response_model=TeamOut,
    summary="Получить команду",
    description="Возвращает mock-профиль команды и её состав.",
    responses={
        404: {
            "model": ErrorOut,
            "description": "Команда не найдена",
            "content": {"application/json": {"example": {"detail": "Команда не найдена"}}},
        }
    },
)
def get_team(team_id: int) -> TeamOut:
    """Профиль команды с участниками, в том числе без аккаунтов."""
    return _fake_team(team_id, "Night Wolves", captain_id=1)


@tournaments_router.get(
    "/{tournament_id}/teams",
    response_model=TournamentTeamsOut,
    summary="Команды турнира",
    description="Возвращает mock-список команд, участвующих в турнире.",
)
def list_tournament_teams(tournament_id: int) -> TournamentTeamsOut:
    """Фиктивные команды турнира."""
    items = [
        _fake_team(1, "Night Wolves", captain_id=1),
        _fake_team(2, "Frostbyte", captain_id=5),
        _fake_team(3, "Red Phoenix", captain_id=8),
    ]
    return TournamentTeamsOut(items=items, total=len(items))


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
            "description": "Заявку подаёт капитан команды",
            "content": {
                "application/json": {"example": {"detail": "Заявку подаёт капитан команды"}}
            },
        },
        409: {
            "model": ErrorOut,
            "description": (
                "Регистрация закрыта, мест нет, команда уже подала заявку или игрок уже заявлен"
            ),
            "content": {
                "application/json": {
                    "examples": {
                        "registration_closed": {
                            "summary": "Регистрация закрыта",
                            "value": {"detail": "Регистрация закрыта"},
                        },
                        "no_places": {
                            "summary": "Мест нет",
                            "value": {"detail": "Мест нет"},
                        },
                        "already_registered": {
                            "summary": "Команда уже подала заявку",
                            "value": {"detail": "Команда уже подала заявку"},
                        },
                        "player_in_another_team": {
                            "summary": "Игрок уже заявлен в другой команде",
                            "value": {"detail": "Игрок {ник} уже заявлен в другой команде"},
                        },
                    }
                }
            },
        },
    },
)
def register_team_for_tournament(
    tournament_id: int,
    reg_in: RegistrationCreate,
    user: CurrentUser,
) -> RegistrationOut:
    """Вернуть фиктивную заявку вошедшего пользователя."""
    _ = user
    return RegistrationOut(
        id=1, tournament_id=tournament_id, team_id=reg_in.team_id, status="pending"
    )


@tournaments_router.get(
    "/{tournament_id}/my-registration",
    response_model=RegistrationOut,
    summary="Моя заявка на турнир",
    description="Возвращает mock-заявку текущего пользователя со статусом approved.",
    responses={
        401: {"model": ErrorOut, "description": "Сначала войдите через Discord"},
        404: {
            "model": ErrorOut,
            "description": "Заявка не найдена",
            "content": {"application/json": {"example": {"detail": "Заявка не найдена"}}},
        },
    },
)
def get_my_registration(
    tournament_id: int,
    user: CurrentUser,
) -> RegistrationOut:
    """Вернуть фиктивный статус заявки вошедшего пользователя."""
    return RegistrationOut(id=1, tournament_id=tournament_id, team_id=user.id, status="approved")
