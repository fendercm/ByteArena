from fastapi import APIRouter, Response
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/auth/discord", tags=["auth"])

@router.get("/login")
def discord_login():
    return 
RedirectResponse(url="https://discord.com/oauth2/authorize?client_id=12345&redirect_uri=http://localhost:8080/api/auth/discord/callback&response_type=code&scope=identify")

@router.get("/callback")
def discord_callback(response: Response):
    response.set_cookie(key="access_token", value="fake_jwt_token_123", 
httponly=True)
    return {"status": "ok", "message": "Успешный вход"}
