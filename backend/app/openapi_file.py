"""Контракт API в backend/openapi.json.

После изменения эндпоинтов или схем пересоберите файл и закоммитьте вместе с кодом:
    python -m app.openapi_file                                # из папки backend
    docker compose exec backend python -m app.openapi_file    # из корня, если бэк в Docker

Тест tests/test_openapi_file.py падает в CI, если файл отстал от кода.
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

OPENAPI_PATH = Path(__file__).resolve().parent.parent / "openapi.json"


def current_spec() -> dict:
    """Контракт, который отдаёт код. Через TestClient с root_path, чтобы в файл попал
    servers: [{"url": "/api"}], как в настоящем /api/openapi.json."""
    return TestClient(app, root_path="/api").get("/api/openapi.json").json()


def write_spec() -> None:
    text = json.dumps(current_spec(), ensure_ascii=False, indent=2) + "\n"
    OPENAPI_PATH.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    write_spec()
    print(f"Сохранено: {OPENAPI_PATH}")
