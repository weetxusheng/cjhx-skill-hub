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
from app.services.skills import download_skill_package, get_public_skill_detail, get_public_skill_list, toggle_favorite, toggle_like

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
    payload = get_public_skill_list(
        db,
        PublicSkillListParams(category=category, q=q, sort=sort, page=page, page_size=page_size),
    )
    return success_response(payload.model_dump(mode="json"))


@router.get("/skills/{slug}")
def get_public_skill(
    slug: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser | None = Depends(get_optional_current_user),
) -> dict:
    payload = get_public_skill_detail(db, slug, current_user)
    return success_response(payload.model_dump(mode="json"))


@router.post("/skills/{skill_id}/favorite")
def favorite_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    payload = toggle_favorite(db, skill_id=skill_id, user=current_user, favorited=True)
    return success_response(payload.model_dump(mode="json"))


@router.delete("/skills/{skill_id}/favorite")
def unfavorite_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    payload = toggle_favorite(db, skill_id=skill_id, user=current_user, favorited=False)
    return success_response(payload.model_dump(mode="json"))


@router.post("/skills/{skill_id}/like")
def like_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    payload = toggle_like(db, skill_id=skill_id, user=current_user, liked=True)
    return success_response(payload.model_dump(mode="json"))


@router.delete("/skills/{skill_id}/like")
def unlike_skill(
    skill_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    payload = toggle_like(db, skill_id=skill_id, user=current_user, liked=False)
    return success_response(payload.model_dump(mode="json"))


@router.get("/skills/{skill_id}/download")
def download_skill(
    skill_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser | None = Depends(get_optional_current_user),
):
    actor_key = str(current_user.id) if current_user else (request.client.host if request.client else "anonymous")
    enforce_rate_limit(scope="public-download", actor_key=actor_key, rule_raw=settings.download_rate_limit)
    response, _ = download_skill_package(db, skill_id=skill_id, current_user=current_user, request=request)
    return response
