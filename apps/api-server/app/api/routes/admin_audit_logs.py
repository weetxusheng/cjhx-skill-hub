from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_permissions
from app.schemas.common import success_response
from app.services.governance import export_audit_logs_csv, list_audit_logs_for_export, list_audit_logs_paginated

router = APIRouter()


@router.get("/audit-logs")
def list_audit_logs(
    actor: str | None = Query(default=None),
    action: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions("admin.audit.view")),
) -> dict:
    payload = list_audit_logs_paginated(
        db,
        actor_query=actor,
        action=action,
        target_type=target_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return success_response(payload.model_dump(mode="json"))


@router.get("/audit-logs/export")
def export_audit_logs(
    actor: str | None = Query(default=None),
    action: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=2000),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions("admin.audit.export")),
) -> Response:
    items = list_audit_logs_for_export(
        db,
        actor_query=actor,
        action=action,
        target_type=target_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    csv_payload = export_audit_logs_csv(items)
    return Response(
        content=csv_payload,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="skill-hub-audit-logs.csv"'},
    )
