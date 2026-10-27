# Сюда импортируются все модели, чтобы Alembic видел их при autogenerate.
# Пример (A, неделя 1):
#   from app.models.user import User
#   from app.models.match import Match
from app.db import Base

__all__ = ["Base"]
