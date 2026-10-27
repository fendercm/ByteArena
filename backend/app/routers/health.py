from fastapi import APIRouter

router = APIRouter(tags=["service"])


@router.get("/health")
def health() -> dict[str, str]:
    """Проверка, что бэкенд запущен."""
    return {"status": "ok"}
