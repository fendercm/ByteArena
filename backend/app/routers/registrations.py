"""Панель организатора: заявки команд и закрытие регистрации."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.auth.dependencies import CurrentUser
from app.db import DbSession
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
from app.models.user import User
from app.routers.tournaments import _out
from app.schemas.common import ErrorOut
from app.schemas.registration import (
    RegistrationAdminList,
    RegistrationAdminOut,
    RegistrationMemberOut,
)
from app.schemas.team import RegistrationUpdate, TeamShort
from app.schemas.tournament import TournamentOut

router = APIRouter(tags=["registrations"])

MIN_TEAMS_TO_CLOSE = 2
ROLE_ORDER = {"captain": 0, "main": 1, "sub": 2}

ORGANIZER_ERRORS = {
    401: {"model": ErrorOut},
    403: {"model": ErrorOut, "description": "Это может только организатор турнира"},
    404: {"model": ErrorOut},
}


def _tournament_for_organizer(
    db: DbSession, tournament_id: int, user: User, *, lock: bool = False
) -> Tournament:
    """Турнир, которым управляет текущий пользователь, иначе 404 или 403.
    lock=True блокирует строку турнира до конца транзакции: две одновременные проверки
    «есть ли места» не пропустят лишнюю команду."""
    tournament = db.get(Tournament, tournament_id, with_for_update=lock)
    if tournament is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Турнир не найден")
    if tournament.organizer_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Это может только организатор турнира",
        )
    return tournament


def _approved_count(db: DbSession, tournament_id: int) -> int:
    return db.scalar(
        select(func.count()).where(
            TournamentTeam.tournament_id == tournament_id, TournamentTeam.status == "approved"
        )
    )


def _registrations(db: DbSession, *where) -> list[RegistrationAdminOut]:
    rows = db.execute(
        select(TournamentTeam, Team).join(Team, Team.id == TournamentTeam.team_id).where(*where)
    ).all()
    members: dict[int, list[TeamMember]] = {}
    team_ids = [team.id for _, team in rows]
    if team_ids:
        for member in db.scalars(select(TeamMember).where(TeamMember.team_id.in_(team_ids))):
            members.setdefault(member.team_id, []).append(member)
    return [
        RegistrationAdminOut(
            id=registration.id,
            tournament_id=registration.tournament_id,
            team=TeamShort(id=team.id, name=team.name),
            status=registration.status,
            members=[
                RegistrationMemberOut(nickname=m.nickname, user_id=m.user_id, role=m.role)
                for m in sorted(members.get(team.id, []), key=lambda m: (ROLE_ORDER[m.role], m.id))
            ],
        )
        for registration, team in sorted(rows, key=lambda row: row[0].id)
    ]


@router.get(
    "/tournaments/{tournament_id}/registrations",
    response_model=RegistrationAdminList,
    responses=ORGANIZER_ERRORS,
)
def list_registrations(
    tournament_id: int, user: CurrentUser, db: DbSession
) -> RegistrationAdminList:
    """Все заявки турнира с составами и статусами в порядке подачи. Только организатор."""
    _tournament_for_organizer(db, tournament_id, user)
    items = _registrations(db, TournamentTeam.tournament_id == tournament_id)
    return RegistrationAdminList(items=items, total=len(items))


@router.patch(
    "/registrations/{registration_id}",
    response_model=RegistrationAdminOut,
    responses={
        **ORGANIZER_ERRORS,
        409: {"model": ErrorOut, "description": "«Мест нет» или «Регистрация закрыта»"},
    },
)
def decide_registration(
    registration_id: int, body: RegistrationUpdate, user: CurrentUser, db: DbSession
) -> RegistrationAdminOut:
    """Подтвердить или отклонить заявку. Только организатор, пока регистрация открыта."""
    registration = db.get(TournamentTeam, registration_id)
    if registration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")
    tournament = _tournament_for_organizer(db, registration.tournament_id, user, lock=True)

    if tournament.status != "registration":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Регистрация закрыта")
    if (
        body.status == "approved"
        and registration.status != "approved"
        and _approved_count(db, tournament.id) >= tournament.max_teams
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Мест нет")

    registration.status = body.status
    db.commit()
    return _registrations(db, TournamentTeam.id == registration_id)[0]


@router.post(
    "/tournaments/{tournament_id}/close-registration",
    response_model=TournamentOut,
    responses={
        **ORGANIZER_ERRORS,
        409: {
            "model": ErrorOut,
            "description": "Регистрация уже закрыта или подтверждено меньше 2 команд",
        },
    },
)
def close_registration(tournament_id: int, user: CurrentUser, db: DbSession) -> TournamentOut:
    """Закрыть регистрацию: статус registration → closed. Нужно минимум 2 подтверждённые команды."""
    tournament = _tournament_for_organizer(db, tournament_id, user, lock=True)
    if tournament.status != "registration":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Регистрация уже закрыта")
    approved = _approved_count(db, tournament.id)
    if approved < MIN_TEAMS_TO_CLOSE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Нужно минимум {MIN_TEAMS_TO_CLOSE} подтверждённые команды",
        )

    tournament.status = "closed"
    db.commit()
    db.refresh(tournament)
    return _out(tournament, teams_count=approved)
