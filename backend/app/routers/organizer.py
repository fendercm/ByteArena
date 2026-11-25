"""Проверка «это может только организатор» для панели, запуска турнира и ввода счёта."""

from fastapi import HTTPException, status

from app.db import DbSession
from app.models.tournament import Tournament
from app.models.user import User
from app.schemas.common import ErrorOut

ORGANIZER_ERRORS = {
    401: {"model": ErrorOut},
    403: {"model": ErrorOut, "description": "Это может только организатор турнира"},
    404: {"model": ErrorOut},
}


def tournament_for_organizer(
    db: DbSession, tournament_id: int, user: User, *, lock: bool = False
) -> Tournament:
    """Турнир, которым управляет текущий пользователь, иначе 404 или 403.
    lock=True блокирует строку турнира до конца транзакции: два одновременных запроса
    (одобрение заявок, запуск, ввод счёта) выполнятся по очереди, а не вперемешку."""
    tournament = db.get(Tournament, tournament_id, with_for_update=lock)
    if tournament is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Турнир не найден")
    if tournament.organizer_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Это может только организатор турнира",
        )
    return tournament
