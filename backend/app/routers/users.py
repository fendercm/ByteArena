from fastapi import APIRouter

from app.auth.dependencies import CurrentUser
from app.models.user import User
from app.schemas.auth import UserMeOut
from app.schemas.common import ErrorOut
from app.schemas.user import UserProfileOut

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
def get_user_profile(user_id: int):
    return UserProfileOut(
        id=user_id,
        nickname="Player123",
        avatar_url=f"https://example.com/avatars/{user_id}.png",
    )
