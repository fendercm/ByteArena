from urllib.parse import urlencode

from fastapi import APIRouter, Response
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/auth/discord", tags=["auth"])


@router.get("/login", status_code=307)
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


@router.get("/callback")
def discord_callback(response: Response):
    response.set_cookie(key="access_token", value="fake_jwt_token_123", httponly=True)
    return {"status": "ok", "message": "Успешный вход"}
