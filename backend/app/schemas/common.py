from datetime import UTC, datetime
from typing import Annotated, Any

from pydantic import AwareDatetime, BaseModel, BeforeValidator


class ErrorOut(BaseModel):
    """Ответ с ошибкой: {"detail": "текст ошибки"}."""

    detail: str


def _assume_utc(value: Any) -> Any:
    # PostgreSQL отдаёт время с поясом, а SQLite в тестах — без. В базе всё хранится в UTC.
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


# Время в ответах API: всегда с часовым поясом, даже если база вернула его без пояса
UtcDatetime = Annotated[AwareDatetime, BeforeValidator(_assume_utc)]
