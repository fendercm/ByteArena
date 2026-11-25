import json

from app.openapi_file import OPENAPI_PATH, current_spec


def test_openapi_json_matches_code() -> None:
    saved = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
    actual = current_spec()

    changed = sorted(
        f"{method.upper()} {path}"
        for path in saved["paths"].keys() | actual["paths"].keys()
        for method in saved["paths"].get(path, {}).keys() | actual["paths"].get(path, {}).keys()
        if saved["paths"].get(path, {}).get(method) != actual["paths"].get(path, {}).get(method)
    )
    schemas = sorted(
        name
        for name in saved["components"]["schemas"].keys() | actual["components"]["schemas"].keys()
        if saved["components"]["schemas"].get(name) != actual["components"]["schemas"].get(name)
    )
    assert saved == actual, (
        "openapi.json отстал от кода. Пересоберите: python -m app.openapi_file "
        f"(из папки backend) и закоммитьте. Эндпоинты: {changed or '—'}; схемы: {schemas or '—'}"
    )
