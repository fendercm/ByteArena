from fastapi import APIRouter
from app.schemas.auth import UserMeOut
from app.schemas.user import UserProfileOut

router = APIRouter(prefix="", tags=["users"])

@router.get("/me", response_model=UserMeOut)
def get_current_user():
    return UserMeOut(id=1, username="Fedor", 
avatar_url="https://example.com/avatar.png")

@router.get("/users/{user_id}", response_model=UserProfileOut)
def get_user_profile(user_id: int):
    return UserProfileOut(id=user_id, username="Player123", rating=1500, 
games_played=42)
