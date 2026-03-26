from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.schemas.common import success_response
from app.services.runtime import readiness_status


router = APIRouter()


@router.get("/live")
def liveness_probe() -> dict:
    return success_response({"status": "ok"})


@router.get("/ready")
def readiness_probe():
    ready, checks = readiness_status()
    payload = success_response({"status": "ready" if ready else "degraded", "checks": checks})
    if ready:
        return payload
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)
