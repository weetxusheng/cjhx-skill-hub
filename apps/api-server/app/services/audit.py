from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.request_context import get_request_id
from app.models.audit_log import AuditLog


def write_audit_log(
    db: Session,
    *,
    actor_user_id: UUID | None,
    action: str,
    target_type: str,
    target_id: UUID | None,
    before_json: dict | None = None,
    after_json: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            request_id=get_request_id(),
            before_json=before_json,
            after_json=after_json,
        )
    )
