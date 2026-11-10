from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  — регистрирует все модели в Base.metadata
from app.auth.security import ACCESS_TOKEN_COOKIE, create_access_token
from app.config import settings
from app.db import Base, get_db
from app.main import app as api
from app.models.user import User


@pytest.fixture
def db() -> Iterator[Session]:
    """Отдельная база SQLite в памяти на каждый тест, чтобы тестам не нужен был PostgreSQL."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    api.dependency_overrides[get_db] = lambda: session
    try:
        yield session
    finally:
        api.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()


@pytest.fixture
def auth_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Настройки входа для тестов: http без https, тестовые ключи Discord и JWT."""
    monkeypatch.setattr(settings, "jwt_secret", "test-secret-" + "x" * 32)
    monkeypatch.setattr(settings, "cookie_secure", False)
    monkeypatch.setattr(settings, "discord_client_id", "test-client")
    monkeypatch.setattr(settings, "discord_client_secret", "test-client-secret")


@pytest.fixture
def client(db: Session, auth_settings: None) -> TestClient:
    """Клиент с базой и настройками входа; запоминает cookie между запросами, как браузер."""
    return TestClient(api, follow_redirects=False)


@pytest.fixture
def user(db: Session) -> User:
    """Игрок в базе, от имени которого работает logged_in."""
    player = User(discord_id="100", nickname="Organizer")
    db.add(player)
    db.commit()
    return player


@pytest.fixture
def logged_in(client: TestClient, user: User) -> TestClient:
    """Клиент, уже вошедший как user: cookie входа выставлена, как после Discord."""
    client.cookies.set(ACCESS_TOKEN_COOKIE, create_access_token(user.id))
    return client
