from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from app.auth.dependencies import CurrentUser
from app.db import DbSession
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
from app.models.user import User
from app.schemas.common import ErrorOut
from app.schemas.team import (
    RegistrationCreate,
    RegistrationOut,
    TeamCreate,
    TeamMemberOut,
    TeamOut,
    TeamProfile,
    TeamProfileCaptain,
    TeamProfileMember,
    TeamProfileTournament,
    TournamentTeamsOut,
)
from app.services.tournament_result import TournamentResult, get_tournament_result

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
    response_model=TeamProfile,
    summary="Получить профиль команды",
    description="Возвращает команду, капитана, состав и турниры с состоянием заявок.",
    responses={
        404: {
            "model": ErrorOut,
            "description": "Команда не найдена",
            "content": {"application/json": {"example": {"detail": "Команда не найдена"}}},
        }
    },
)
def get_team(team_id: int, db: DbSession) -> TeamProfile:
    """Публичный профиль команды с зарегистрированными и незарегистрированными игроками."""
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не найдена",
        )

    captain = db.get(User, team.captain_id)
    if captain is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не найдена",
        )

    member_rows = db.scalars(select(TeamMember).where(TeamMember.team_id == team.id)).all()
    role_order = {"captain": 0, "main": 1, "sub": 2}
    member_rows.sort(key=lambda member: (role_order[member.role], member.id))

    members = []
    for member in member_rows:
        player = db.get(User, member.user_id) if member.user_id is not None else None
        members.append(
            TeamProfileMember(
                nickname=member.nickname,
                user_id=member.user_id,
                avatar_url=player.avatar_url if player is not None else None,
                role=member.role,
            )
        )

    tournament_rows = db.execute(
        select(Tournament, TournamentTeam)
        .join(TournamentTeam, TournamentTeam.tournament_id == Tournament.id)
        .where(TournamentTeam.team_id == team.id)
        .order_by(Tournament.starts_at.desc(), Tournament.id.desc())
    ).all()

    tournaments = []
    for tournament, registration in tournament_rows:
        # итог турнира есть только у команды, чью заявку одобрили
        outcome = (
            get_tournament_result(db, tournament, team.id)
            if registration.status == "approved"
            else TournamentResult(None)
        )
        tournaments.append(
            TeamProfileTournament(
                id=tournament.id,
                title=tournament.title,
                starts_at=tournament.starts_at,
                status=tournament.status,
                application_status=registration.status,
                result=outcome.result,
                eliminated_round=outcome.eliminated_round,
            )
        )

    return TeamProfile(
        id=team.id,
        name=team.name,
        captain=TeamProfileCaptain(id=captain.id, nickname=captain.nickname),
        members=members,
        tournaments=tournaments,
    )


@tournaments_router.get(
    "/{tournament_id}/teams",
    response_model=TournamentTeamsOut,
    summary="Команды турнира",
)
def list_tournament_teams(tournament_id: int, db: DbSession) -> TournamentTeamsOut:
    """Подтверждённые команды турнира с составами."""
    if db.get(Tournament, tournament_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Турнир не найден")

    teams = db.scalars(
        select(Team)
        .join(TournamentTeam, TournamentTeam.team_id == Team.id)
        .where(
            TournamentTeam.tournament_id == tournament_id,
            TournamentTeam.status == "approved",
        )
        .order_by(Team.name, Team.id)
    ).all()

    team_ids = [team.id for team in teams]
    members_by_team: dict[int, list[TeamMember]] = {team_id: [] for team_id in team_ids}
    if team_ids:
        role_order = {"captain": 0, "main": 1, "sub": 2}
        for member in db.scalars(select(TeamMember).where(TeamMember.team_id.in_(team_ids))):
            members_by_team[member.team_id].append(member)

    items = [
        TeamOut(
            id=team.id,
            name=team.name,
            captain_id=team.captain_id,
            members=[
                TeamMemberOut(nickname=member.nickname, user_id=member.user_id, role=member.role)
                for member in sorted(
                    members_by_team[team.id],
                    key=lambda member: (role_order[member.role], member.id),
                )
            ],
        )
        for team in teams
    ]
    return TournamentTeamsOut(items=items, total=len(items))


@tournaments_router.post(
    "/{tournament_id}/registrations",
    response_model=RegistrationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Подать заявку на турнир",
    description="Создаёт заявку команды со статусом pending.",
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
                "Регистрация закрыта, мест нет, команда уже подала заявку " "или игрок уже заявлен"
            ),
            "content": {
                "application/json": {
                    "examples": {
                        "registration_closed": {
                            "summary": "Регистрация закрыта",
                            "value": {"detail": "Регистрация закрыта"},
                        },
                        "no_slots": {
                            "summary": "Мест нет",
                            "value": {"detail": "Мест нет"},
                        },
                        "duplicate_registration": {
                            "summary": "Команда уже подала заявку",
                            "value": {"detail": "Команда уже подала заявку"},
                        },
                        "player_already_registered": {
                            "summary": "Игрок уже заявлен в другой команде",
                            "value": {"detail": "Игрок Alpha уже заявлен в другой команде"},
                        },
                    }
                }
            },
        },
        404: {"model": ErrorOut, "description": "Турнир или команда не найдены"},
    },
)
def register_team_for_tournament(
    tournament_id: int,
    reg_in: RegistrationCreate,
    user: CurrentUser,
    db: DbSession,
) -> RegistrationOut:
    """Подать заявку команды на турнир после всех проверок регистрации."""
    tournament = db.get(Tournament, tournament_id, with_for_update=True)
    if tournament is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Турнир не найден")
    if tournament.status != "registration":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Регистрация закрыта")

    team = db.get(Team, reg_in.team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Команда не найдена")
    if team.captain_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Заявку подаёт капитан команды",
        )

    approved_count = db.scalar(
        select(func.count())
        .select_from(TournamentTeam)
        .where(
            TournamentTeam.tournament_id == tournament_id,
            TournamentTeam.status == "approved",
        )
    )
    if approved_count >= tournament.max_teams:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Мест нет")

    if (
        db.scalar(
            select(TournamentTeam.id).where(
                TournamentTeam.tournament_id == tournament_id,
                TournamentTeam.team_id == reg_in.team_id,
            )
        )
        is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Команда уже подала заявку",
        )

    current_member = aliased(TeamMember)
    other_member = aliased(TeamMember)
    conflict_nickname = db.execute(
        select(current_member.nickname)
        .join(other_member, other_member.user_id == current_member.user_id)
        .join(TournamentTeam, TournamentTeam.team_id == other_member.team_id)
        .where(
            current_member.team_id == reg_in.team_id,
            current_member.user_id.is_not(None),
            other_member.team_id != reg_in.team_id,
            TournamentTeam.tournament_id == tournament_id,
            TournamentTeam.status != "rejected",  # Исключаем отклонённые заявки
        )
        .limit(1)
    ).scalar_one_or_none()
    if conflict_nickname is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Игрок {conflict_nickname} уже заявлен в другой команде",
        )

    registration = TournamentTeam(
        tournament_id=tournament_id,
        team_id=reg_in.team_id,
        status="pending",
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return RegistrationOut(
        id=registration.id,
        tournament_id=registration.tournament_id,
        team_id=registration.team_id,
        status=registration.status,
    )


@tournaments_router.get(
    "/{tournament_id}/my-registration",
    response_model=RegistrationOut,
    summary="Моя заявка на турнир",
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
    db: DbSession,
) -> RegistrationOut:
    """Вернуть заявку команды, в состав которой входит текущий пользователь."""
    from app.models.tournament_team import TournamentTeam

    registration = db.execute(
        select(TournamentTeam)
        .join(TeamMember, TeamMember.team_id == TournamentTeam.team_id)
        .where(
            TournamentTeam.tournament_id == tournament_id,
            TeamMember.user_id == user.id,
        )
        .order_by(TournamentTeam.id)
        .limit(1)
    ).scalar_one_or_none()
    if registration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")
    return RegistrationOut(
        id=registration.id,
        tournament_id=registration.tournament_id,
        team_id=registration.team_id,
        status=registration.status,
    )
