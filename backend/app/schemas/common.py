from pydantic import BaseModel


class ErrorOut(BaseModel):
    """Ответ с ошибкой: {"detail": "текст ошибки"}."""

    detail: str
