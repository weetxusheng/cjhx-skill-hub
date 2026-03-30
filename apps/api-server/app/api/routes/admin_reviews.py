"""审核工作台：待审队列与审核历史时间线。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_permissions
from app.schemas.common import success_response
from app.services.skills import get_review_history_feed, get_review_queue

router = APIRouter()


@router.get("/reviews")
def list_reviews(
    category: str | None = Query(default=None),
    created_by: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.review")),
) -> dict:
    """当前审核员可见的待审版本队列（可按分类与创建者筛选）。"""
    payload = get_review_queue(db, category=category, created_by=created_by, current_user=current_user)
    return success_response([item.model_dump(mode="json") for item in payload])


@router.get("/reviews/pending")
def list_pending_reviews(
    category: str | None = Query(default=None),
    created_by: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.review")),
) -> dict:
    """与 `/reviews` 一致，保留兼容路径。"""
    payload = get_review_queue(db, category=category, created_by=created_by, current_user=current_user)
    return success_response([item.model_dump(mode="json") for item in payload])


@router.get("/reviews/history")
def list_review_history(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.view")),
) -> dict:
    """审核动作历史 feed（时间线）；需 skill.view 以缩小可见范围。"""
    payload = get_review_history_feed(db, current_user=current_user)
    return success_response([item.model_dump(mode="json") for item in payload])
