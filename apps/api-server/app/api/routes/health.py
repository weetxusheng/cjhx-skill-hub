"""Kubernetes 风格存活与就绪探针（就绪会检查依赖）。"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.schemas.common import success_response
from app.services.runtime import readiness_status


router = APIRouter()


@router.get("/live")
def liveness_probe() -> dict:
    """存活探针：进程可响应即返回 ok。"""
    return success_response({"status": "ok"})


@router.get("/ready")
def readiness_probe():
    """就绪探针：依赖未就绪时返回 503 与检查结果。"""
    ready, checks = readiness_status()
    payload = success_response({"status": "ready" if ready else "degraded", "checks": checks})
    if ready:
        return payload
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)
