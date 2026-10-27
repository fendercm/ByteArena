from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей. Модели лежат в app/models/."""


def get_db() -> Iterator[Session]:
    """Зависимость FastAPI: сессия БД на один запрос."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
