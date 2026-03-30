"""门户公开技能：列表、详情、收藏/点赞、包下载与上传中心记录。"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, get_optional_current_user, get_current_user
from app.core.config import get_settings
from app.core.rate_limit import enforce_rate_limit
from app.repositories.skills import PublicSkillListParams
from app.schemas.common import success_response
from app.services.skills import (
    download_skill_package,
    get_portal_upload_center_records,
    get_public_skill_detail,
    get_public_skill_list,
    toggle_favorite,
    toggle_like,
)

router = APIRouter()
settings = get_settings()


@router.get("/skills")
def list_public_skills(
    category: str | None = Query(default=None),
    q: str | None = Query(default=None),
    sort: Literal["latest", "downloads", "favorites", "name"] = Query(default="latest"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=48),
    db: Session = Depends(get_db),
) -> dict:
    """分页列出已发布技能，支持分类、关键词与排序。"""
    payload = get_public_skill_list(
        db,
        PublicSkillListParams(category=category, q=q, sort=sort, page=page, page_size=page_size),
    )
    return success_response(payload.model_dump(mode="json"))


@router.get("/upload-center/records")
def list_portal_upload_center_records(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """当前用户在各技能上的上传与版本状态摘要（需登录）。"""
    payload = get_portal_upload_center_records(
        db,
        page=page,
        page_size=page_size,
        current_user=current_user,
    )
    return success_response(payload.model_dump(mode="json"))


@router.get("/skills/{slug}")
def get_public_skill(
    slug: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser | None = Depends(get_optional_current_user),
) -> dict:
    """按 slug 返回技能详情；登录用户可带个性化字段（如是否已收藏）。"""
    payload = get_public_skill_detail(db, slug, current_user)
    return success_response(payload.model_dump(mode="json"))


@router.post("/skills/{skill_id}/favorite")
def favorite_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """将技能加入当前用户收藏。"""
    payload = toggle_favorite(db, skill_id=skill_id, user=current_user, favorited=True)
    return success_response(payload.model_dump(mode="json"))


@router.delete("/skills/{skill_id}/favorite")
def unfavorite_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """取消收藏。"""
    payload = toggle_favorite(db, skill_id=skill_id, user=current_user, favorited=False)
    return success_response(payload.model_dump(mode="json"))


@router.post("/skills/{skill_id}/like")
def like_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """点赞（幂等计数由服务层处理）。"""
    payload = toggle_like(db, skill_id=skill_id, user=current_user, liked=True)
    return success_response(payload.model_dump(mode="json"))


@router.delete("/skills/{skill_id}/like")
def unlike_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """取消点赞。"""
    payload = toggle_like(db, skill_id=skill_id, user=current_user, liked=False)
    return success_response(payload.model_dump(mode="json"))


@router.get("/skills/{skill_id}/download")
def download_skill(
    skill_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser | None = Depends(get_optional_current_user),
):
    """下载当前已发布版本的包文件；匿名用户按 IP、登录用户按用户 ID 限流。"""
    actor_key = str(current_user.id) if current_user else (request.client.host if request.client else "anonymous")
    enforce_rate_limit(scope="public-download", actor_key=actor_key, rule_raw=settings.download_rate_limit)
    response, _ = download_skill_package(db, skill_id=skill_id, current_user=current_user, request=request)
    return response
