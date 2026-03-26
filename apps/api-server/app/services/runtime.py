from __future__ import annotations

from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.redis import is_redis_available
from app.services.storage import storage_ready_check


def readiness_status() -> tuple[bool, dict[str, dict[str, str]]]:
    checks: dict[str, dict[str, str]] = {}

    try:
        with SessionLocal() as session:
            session.execute(text("select 1"))
        checks["database"] = {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        checks["database"] = {"status": "error", "detail": str(exc)}

    redis_ok = is_redis_available()
    checks["redis"] = {"status": "ok" if redis_ok else "error"}
    if not redis_ok:
        checks["redis"]["detail"] = "Redis ping failed"

    storage_ok, storage_detail = storage_ready_check()
    checks["storage"] = {"status": "ok" if storage_ok else "error"}
    if storage_detail != "ok":
        checks["storage"]["detail"] = storage_detail

    ready = all(item["status"] == "ok" for item in checks.values())
    return ready, checks
