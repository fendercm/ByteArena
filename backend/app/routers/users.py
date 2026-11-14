from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.auth.dependencies import CurrentUser
from app.db import DbSession
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.tournament import Tournament
from app.models.tournament_team import TournamentTeam
from app.models.user import User
from app.schemas.auth import UserMeOut
from app.schemas.common import ErrorOut
from app.schemas.team import TeamShort
from app.schemas.user import TournamentProfileOut, UserProfileOut

router = APIRouter(prefix="", tags=["users"])


@router.get("/me", response_model=UserMeOut, responses={401: {"model": ErrorOut}})
def read_me(user: CurrentUser) -> User:
    """Кто сейчас вошёл. Без входа — 401."""
    return user


@router.get(
    "/users/{user_id}",
    response_model=UserProfileOut,
    responses={404: {"model": ErrorOut}},
)
def get_user_profile(user_id: int, db: DbSession) -> UserProfileOut:
    """Публичный профиль игрока с его командой и турнирами."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Игрок не найден",
        )

    team = db.scalar(
        select(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user_id)
        .order_by(Team.id)
        .limit(1)
    )

    tournaments = db.scalars(
        select(Tournament)
        .join(TournamentTeam, TournamentTeam.tournament_id == Tournament.id)
        .join(TeamMember, TeamMember.team_id == TournamentTeam.team_id)
        .where(
            TeamMember.user_id == user_id,
            TournamentTeam.status == "approved",
        )
        .distinct()
        .order_by(Tournament.starts_at.desc())
    ).all()

    return UserProfileOut(
        id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        team=TeamShort(id=team.id, name=team.name) if team else None,
        tournaments=[
            TournamentProfileOut(id=tournament.id, title=tournament.title)
            for tournament in tournaments
        ],
    )
