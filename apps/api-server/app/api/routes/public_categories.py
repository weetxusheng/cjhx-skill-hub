"""门户公开分类列表（带缓存与可见技能数）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.category import Category
from app.models.skill import Skill
from app.schemas.common import success_response
from app.services.cache import get_cached_json, set_cached_json

router = APIRouter()
settings = get_settings()


@router.get("/categories")
def list_public_categories(db: Session = Depends(get_db)) -> dict:
    """返回可见分类及每类已发布技能数量；命中 Redis 缓存则直接返回。"""
    cache_key = "public:categories"
    cached = get_cached_json(cache_key)
    if cached is not None:
        return success_response(cached)

    query = (
        select(
            Category.id,
            Category.name,
            Category.slug,
            Category.icon,
            Category.description,
            Category.sort_order,
            Category.is_visible,
            func.count(Skill.id).label("skill_count"),
        )
        .select_from(Category)
        .outerjoin(
            Skill,
            and_(
                Skill.category_id == Category.id,
                Skill.status == "active",
                Skill.current_published_version_id.is_not(None),
            ),
        )
        .where(Category.is_visible.is_(True))
        .group_by(
            Category.id,
            Category.name,
            Category.slug,
            Category.icon,
            Category.description,
            Category.sort_order,
            Category.is_visible,
        )
        .order_by(Category.sort_order.asc(), Category.name.asc())
    )

    items = [
        {
            "id": row.id,
            "name": row.name,
            "slug": row.slug,
            "icon": row.icon,
            "description": row.description,
            "sort_order": row.sort_order,
            "is_visible": row.is_visible,
            "skill_count": row.skill_count,
        }
        for row in db.execute(query)
    ]
    set_cached_json(cache_key, items, settings.categories_cache_ttl_seconds)
    return success_response(items)
