from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token
from app.config import settings
from app.db import get_db
from app.models.user import User
from app.schemas.auth import UserMeOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/discord/login", status_code=307)
def discord_login():
    query = urlencode(
        {
            "client_id": "12345",
            "redirect_uri": "http://localhost:8080/api/auth/discord/callback",
            "response_type": "code",
            "scope": "identify",
        }
    )
    return RedirectResponse(url=f"https://discord.com/oauth2/authorize?{query}")


@router.get("/discord/callback")
def discord_callback(response: Response):
    response.set_cookie(key="access_token", value="fake_jwt_token_123", httponly=True)
    return {"status": "ok", "message": "Успешный вход"}


@router.get("/me", response_model=UserMeOut)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/debug-login/{user_id}")
def debug_login(user_id: int, response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    if not settings.debug_auth_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    token = create_access_token({"sub": str(user.id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    return {"message": "Debug login successful"}
