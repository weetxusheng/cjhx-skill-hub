from __future__ import annotations

from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.redis import is_redis_available
from app.services.storage import storage_ready_check


def readiness_status() -> tuple[bool, dict[str, dict[str, str]]]:
    """执行运行时就绪检查并返回聚合结果。

    检查项:
    - database: 通过 `select 1` 验证数据库可达。
    - redis: 通过 ping 检查缓存可达。
    - storage: 执行存储后端健康探针。

    返回:
    - (ready, checks)
      - ready: 所有检查项均为 ok 时为 True。
      - checks: 每项包含 status 与可选 detail。
    """
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
