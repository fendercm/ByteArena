from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки из переменных окружения (в Docker их передаёт docker-compose из .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://bytearena:bytearena@localhost:5432/bytearena"
    discord_client_id: str = "1565087685079728128"
    discord_client_secret: str = "-1asyD8Q77ZEEHjbgEIqOVNQr4yNw16f"
    discord_redirect_uri: str = "http://localhost/api/auth/discord/callback"


settings = Settings()
