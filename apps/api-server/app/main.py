from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.health import router as health_router
from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.request_context import set_request_id

settings = get_settings()
configure_logging()
logger = logging.getLogger("skillhub.api")

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get(settings.request_id_header) or str(uuid4())
    set_request_id(request_id)
    request.state.request_id = request_id
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )
    response.headers[settings.request_id_header] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "interest-cohort=()"
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "http_error",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": exc.status_code,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "detail": exc.detail, "request_id": request_id},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.exception(
        "unhandled_error",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": 500, "message": "服务内部错误", "detail": "服务内部错误", "request_id": request_id},
    )

app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(health_router, prefix="/health", tags=["health"])
