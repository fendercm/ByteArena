from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки из переменных окружения (в Docker их передаёт docker-compose из .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://bytearena:bytearena@localhost:5432/bytearena"
    discord_client_id: str = ""
    discord_client_secret: str = ""
    discord_redirect_uri: str = "http://localhost:8080/api/auth/discord/callback"
    # секрет подписи токенов входа; сгенерировать: openssl rand -hex 32
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    # cookie только по https; локально по http нужно COOKIE_SECURE=false
    cookie_secure: bool = True
    # временный вход без Discord для разработки: POST /api/auth/debug-login/{user_id}
    debug_auth_enabled: bool = False


settings = Settings()
