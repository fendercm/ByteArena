from fastapi import APIRouter, HTTPException, Query, status
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
from app.schemas.user import TournamentProfileOut, UserProfileOut, UserSearchOut

router = APIRouter(prefix="", tags=["users"])


@router.get(
    "/users/search",
    response_model=list[UserSearchOut],
    summary="Поиск игроков",
    description="Подсказки по нику. Для запроса короче двух символов возвращается пустой список.",
)
def search_users(
    db: DbSession,
    q: str = Query(default="", description="Поисковая строка; минимум 2 символа для подсказок."),
) -> list[UserSearchOut]:
    """Найти игроков по началу ника; символы LIKE в запросе считаются обычным текстом."""
    q = q.strip()
    if len(q) < 2:
        return []
    safe = q.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
    users = db.scalars(
        select(User)
        .where(User.nickname.ilike(f"{safe}%", escape="\\"))
        .order_by(User.nickname)
        .limit(10)
    ).all()
    return [
        UserSearchOut(id=user.id, nickname=user.nickname, avatar_url=user.avatar_url)
        for user in users
    ]


def _user_team(db: DbSession, user_id: int) -> TeamShort | None:
    """Команда игрока; если команд несколько, берём самую раннюю."""
    team = db.scalar(
        select(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user_id)
        .order_by(Team.id)
        .limit(1)
    )
    return TeamShort(id=team.id, name=team.name) if team else None


@router.get("/me", response_model=UserMeOut, responses={401: {"model": ErrorOut}})
def read_me(user: CurrentUser, db: DbSession) -> UserMeOut:
    """Кто сейчас вошёл и его команда. Без входа — 401."""
    return UserMeOut(
        id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        team=_user_team(db, user.id),
    )


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
        team=_user_team(db, user_id),
        tournaments=[
            TournamentProfileOut(id=tournament.id, title=tournament.title)
            for tournament in tournaments
        ],
    )
