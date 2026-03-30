"""待发布队列：已通过审核、待执行发布的版本列表。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_permissions
from app.schemas.common import success_response
from app.services.skills import get_pending_releases

router = APIRouter()


@router.get("/releases/pending")
def list_pending_releases(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.publish")),
) -> dict:
    """列出当前用户有权发布的、处于待发布状态的版本。"""
    payload = get_pending_releases(db, current_user=current_user)
    return success_response([item.model_dump(mode="json") for item in payload])
