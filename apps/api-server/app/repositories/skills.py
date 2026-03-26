from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.favorite import Favorite
from app.models.download_log import DownloadLog
from app.models.role import Role
from app.models.skill import Skill
from app.models.skill_like import SkillLike
from app.models.skill_role_grant import SkillRoleGrant
from app.models.skill_user_grant import SkillUserGrant
from app.models.skill_version import SkillVersion
from app.models.user import User
from app.models.user_role import UserRole
from app.models.version_review import VersionReview

PublicSkillSort = Literal["latest", "downloads", "favorites", "name"]


@dataclass(slots=True)
class PublicSkillListParams:
    category: str | None = None
    q: str | None = None
    sort: PublicSkillSort = "latest"
    page: int = 1
    page_size: int = 12


@dataclass(slots=True)
class AdminSkillListParams:
    category: str | None = None
    q: str | None = None
    status: str | None = None
    page: int = 1
    page_size: int = 10


def _apply_shared_filters(query: Select, *, category: str | None, q: str | None) -> Select:
    if category:
        query = query.where(Category.slug == category)

    if q:
        keyword = f"%{q.strip()}%"
        query = query.where(
            or_(
                Skill.name.ilike(keyword),
                Skill.slug.ilike(keyword),
                Skill.summary.ilike(keyword),
                Skill.description.ilike(keyword),
                Category.name.ilike(keyword),
            )
        )

    return query


def _count_rows(db: Session, query: Select) -> int:
    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    return db.execute(count_query).scalar_one()


def list_public_skills_paginated(db: Session, params: PublicSkillListParams) -> tuple[list[dict], int]:
    query = (
        select(
            Skill.id,
            Skill.name,
            Skill.slug,
            Skill.summary,
            Skill.latest_version_no,
            Skill.download_count,
            Skill.favorite_count,
            Skill.like_count,
            Skill.published_at,
            Skill.icon_file_id,
            Category.name.label("category_name"),
            Category.slug.label("category_slug"),
        )
        .join(Category, Category.id == Skill.category_id)
        .where(
            Skill.status == "active",
            Skill.current_published_version_id.is_not(None),
        )
    )
    query = _apply_shared_filters(query, category=params.category, q=params.q)

    if params.sort == "downloads":
        query = query.order_by(Skill.download_count.desc(), Skill.name.asc())
    elif params.sort == "favorites":
        query = query.order_by(Skill.favorite_count.desc(), Skill.name.asc())
    elif params.sort == "name":
        query = query.order_by(Skill.name.asc())
    else:
        query = query.order_by(Skill.published_at.desc().nullslast(), Skill.name.asc())

    total = _count_rows(db, query)
    offset = (params.page - 1) * params.page_size
    rows = db.execute(query.offset(offset).limit(params.page_size)).all()
    items = [
        {
            "id": row.id,
            "name": row.name,
            "slug": row.slug,
            "summary": row.summary,
            "category_name": row.category_name,
            "category_slug": row.category_slug,
            "latest_version_no": row.latest_version_no,
            "download_count": row.download_count,
            "favorite_count": row.favorite_count,
            "like_count": row.like_count,
            "published_at": row.published_at,
            "icon_file_id": row.icon_file_id,
        }
        for row in rows
    ]
    return items, total


def list_admin_skills_paginated(db: Session, params: AdminSkillListParams) -> tuple[list[dict], int]:
    return _list_admin_skills(db, params, paginate=True)


def list_admin_skills_all(db: Session, params: AdminSkillListParams) -> list[dict]:
    items, _ = _list_admin_skills(db, params, paginate=False)
    return items


def _list_admin_skills(db: Session, params: AdminSkillListParams, *, paginate: bool) -> tuple[list[dict], int]:
    latest_version_status_sq = (
        select(SkillVersion.review_status)
        .where(SkillVersion.skill_id == Skill.id)
        .order_by(SkillVersion.created_at.desc())
        .limit(1)
        .scalar_subquery()
    )
    owner_name_sq = select(User.display_name).where(User.id == Skill.owner_user_id).limit(1).scalar_subquery()
    current_published_version_sq = (
        select(SkillVersion.version)
        .where(SkillVersion.id == Skill.current_published_version_id)
        .limit(1)
        .scalar_subquery()
    )
    pending_review_count_sq = (
        select(func.count())
        .select_from(SkillVersion)
        .where(SkillVersion.skill_id == Skill.id, SkillVersion.review_status == "submitted")
        .scalar_subquery()
    )
    pending_release_count_sq = (
        select(func.count())
        .select_from(SkillVersion)
        .where(SkillVersion.skill_id == Skill.id, SkillVersion.review_status == "approved")
        .scalar_subquery()
    )
    query = (
        select(
            Skill.id,
            Skill.name,
            Skill.slug,
            Skill.status,
            Skill.latest_version_no,
            Skill.current_published_version_id,
            latest_version_status_sq.label("latest_version_status"),
            current_published_version_sq.label("current_published_version"),
            owner_name_sq.label("owner_display_name"),
            pending_review_count_sq.label("pending_review_count"),
            pending_release_count_sq.label("pending_release_count"),
            Skill.like_count,
            Skill.favorite_count,
            Skill.download_count,
            Skill.created_at,
            Skill.updated_at,
            Skill.published_at,
            Category.name.label("category_name"),
            Category.slug.label("category_slug"),
        )
        .join(Category, Category.id == Skill.category_id)
    )
    query = _apply_shared_filters(query, category=params.category, q=params.q)

    if params.status:
        query = query.where(Skill.status == params.status)

    query = query.order_by(Skill.updated_at.desc(), Skill.name.asc())
    total = _count_rows(db, query)
    if paginate:
        offset = (params.page - 1) * params.page_size
        rows = db.execute(query.offset(offset).limit(params.page_size)).all()
    else:
        rows = db.execute(query).all()
    items = [
        {
            "id": row.id,
            "name": row.name,
            "slug": row.slug,
            "status": row.status,
            "category_name": row.category_name,
            "category_slug": row.category_slug,
            "latest_version_no": row.latest_version_no,
            "current_published_version_id": row.current_published_version_id,
            "latest_version_status": row.latest_version_status,
            "current_published_version": row.current_published_version,
            "owner_display_name": row.owner_display_name,
            "pending_review_count": row.pending_review_count,
            "pending_release_count": row.pending_release_count,
            "like_count": row.like_count,
            "favorite_count": row.favorite_count,
            "download_count": row.download_count,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "published_at": row.published_at,
        }
        for row in rows
    ]
    return items, total


def get_skill_detail_by_slug(db: Session, slug: str) -> dict | None:
    row = db.execute(
        select(
            Skill.id,
            Skill.name,
            Skill.slug,
            Skill.summary,
            Skill.description,
            Skill.status,
            Skill.category_id,
            Skill.latest_version_no,
            Skill.current_published_version_id,
            Skill.download_count,
            Skill.favorite_count,
            Skill.like_count,
            Skill.owner_user_id,
            Skill.published_at,
            Skill.created_at,
            Skill.updated_at,
            Category.name.label("category_name"),
            Category.slug.label("category_slug"),
        )
        .join(Category, Category.id == Skill.category_id)
        .where(Skill.slug == slug)
    ).mappings().first()
    return dict(row) if row else None


def get_skill_detail_by_id(db: Session, skill_id: str) -> dict | None:
    row = db.execute(
        select(
            Skill.id,
            Skill.name,
            Skill.slug,
            Skill.summary,
            Skill.description,
            Skill.status,
            Skill.category_id,
            Skill.latest_version_no,
            Skill.current_published_version_id,
            Skill.download_count,
            Skill.favorite_count,
            Skill.like_count,
            Skill.owner_user_id,
            Skill.published_at,
            Skill.created_at,
            Skill.updated_at,
            Category.name.label("category_name"),
            Category.slug.label("category_slug"),
        )
        .join(Category, Category.id == Skill.category_id)
        .where(Skill.id == skill_id)
    ).mappings().first()
    return dict(row) if row else None


def get_version_summaries_for_skill(db: Session, skill_id: str, *, only_published: bool = False) -> list[dict]:
    query = select(
        SkillVersion.id,
        SkillVersion.version,
        SkillVersion.review_status,
        SkillVersion.created_at,
        SkillVersion.published_at,
    ).where(SkillVersion.skill_id == skill_id)
    if only_published:
        query = query.where(SkillVersion.review_status == "published")
    query = query.order_by(SkillVersion.created_at.desc())
    return [dict(row) for row in db.execute(query).mappings()]


def get_version_detail(db: Session, version_id: str) -> dict | None:
    row = db.execute(
        select(
            SkillVersion.id,
            SkillVersion.skill_id,
            SkillVersion.version,
            SkillVersion.manifest_json,
            SkillVersion.usage_guide_json,
            SkillVersion.readme_markdown,
            SkillVersion.changelog,
            SkillVersion.install_notes,
            SkillVersion.breaking_changes,
            SkillVersion.source_type,
            SkillVersion.review_status,
            SkillVersion.review_comment,
            SkillVersion.reviewed_by,
            SkillVersion.reviewed_at,
            SkillVersion.published_by,
            SkillVersion.published_at,
            SkillVersion.created_by,
            SkillVersion.created_at,
            SkillVersion.updated_at,
        ).where(SkillVersion.id == version_id)
    ).mappings().first()
    return dict(row) if row else None


def get_review_records_for_skill(db: Session, skill_id: str) -> list[dict]:
    query = (
        select(
            VersionReview.id,
            VersionReview.action,
            VersionReview.comment,
            VersionReview.operator_user_id,
            VersionReview.created_at,
            User.display_name.label("operator_display_name"),
        )
        .join(SkillVersion, SkillVersion.id == VersionReview.skill_version_id)
        .join(User, User.id == VersionReview.operator_user_id)
        .where(SkillVersion.skill_id == skill_id)
        .order_by(VersionReview.created_at.desc())
    )
    return [dict(row) for row in db.execute(query).mappings()]


def get_review_records_for_version(db: Session, version_id: str) -> list[dict]:
    query = (
        select(
            VersionReview.id,
            VersionReview.action,
            VersionReview.comment,
            VersionReview.operator_user_id,
            VersionReview.created_at,
            User.display_name.label("operator_display_name"),
        )
        .join(User, User.id == VersionReview.operator_user_id)
        .where(VersionReview.skill_version_id == version_id)
        .order_by(VersionReview.created_at.desc())
    )
    return [dict(row) for row in db.execute(query).mappings()]


def get_skill_role_grants(db: Session, skill_id: str) -> list[dict]:
    query = (
        select(
            SkillRoleGrant.id,
            SkillRoleGrant.role_id.label("target_id"),
            Role.name.label("target_name"),
            SkillRoleGrant.permission_scope,
            SkillRoleGrant.created_at,
        )
        .join(Role, Role.id == SkillRoleGrant.role_id)
        .where(SkillRoleGrant.skill_id == skill_id)
        .order_by(SkillRoleGrant.created_at.asc())
    )
    return [{**dict(row), "target_type": "role"} for row in db.execute(query).mappings()]


def get_skill_user_grants(db: Session, skill_id: str) -> list[dict]:
    query = (
        select(
            SkillUserGrant.id,
            SkillUserGrant.user_id.label("target_id"),
            User.display_name.label("target_name"),
            SkillUserGrant.permission_scope,
            SkillUserGrant.created_at,
        )
        .join(User, User.id == SkillUserGrant.user_id)
        .where(SkillUserGrant.skill_id == skill_id)
        .order_by(SkillUserGrant.created_at.asc())
    )
    return [{**dict(row), "target_type": "user"} for row in db.execute(query).mappings()]


def get_skill_pending_reviews(db: Session, *, category: str | None = None, created_by: str | None = None) -> list[dict]:
    latest_comment_sq = (
        select(VersionReview.comment)
        .where(VersionReview.skill_version_id == SkillVersion.id)
        .order_by(VersionReview.created_at.desc())
        .limit(1)
        .scalar_subquery()
    )
    latest_action_at_sq = (
        select(VersionReview.created_at)
        .where(VersionReview.skill_version_id == SkillVersion.id)
        .order_by(VersionReview.created_at.desc())
        .limit(1)
        .scalar_subquery()
    )
    query = (
        select(
            SkillVersion.id.label("version_id"),
            Skill.id.label("skill_id"),
            Skill.name.label("skill_name"),
            Skill.slug.label("skill_slug"),
            SkillVersion.version,
            Category.name.label("category_name"),
            User.display_name.label("created_by_display_name"),
            SkillVersion.created_at,
            SkillVersion.review_status,
            latest_comment_sq.label("latest_review_comment"),
            latest_action_at_sq.label("latest_action_at"),
        )
        .join(Skill, Skill.id == SkillVersion.skill_id)
        .join(Category, Category.id == Skill.category_id)
        .join(User, User.id == SkillVersion.created_by)
        .where(SkillVersion.review_status == "submitted")
        .order_by(SkillVersion.created_at.desc())
    )
    if category:
        query = query.where(Category.name == category)
    if created_by:
        query = query.where(User.display_name.ilike(f"%{created_by.strip()}%"))
    return [dict(row) for row in db.execute(query).mappings()]


def get_skill_pending_releases(db: Session) -> list[dict]:
    latest_comment_sq = (
        select(VersionReview.comment)
        .where(VersionReview.skill_version_id == SkillVersion.id, VersionReview.action == "approve")
        .order_by(VersionReview.created_at.desc())
        .limit(1)
        .scalar_subquery()
    )
    approved_at_sq = (
        select(VersionReview.created_at)
        .where(VersionReview.skill_version_id == SkillVersion.id, VersionReview.action == "approve")
        .order_by(VersionReview.created_at.desc())
        .limit(1)
        .scalar_subquery()
    )
    query = (
        select(
            SkillVersion.id.label("version_id"),
            Skill.id.label("skill_id"),
            Skill.name.label("skill_name"),
            Skill.slug.label("skill_slug"),
            SkillVersion.version,
            Category.name.label("category_name"),
            User.display_name.label("created_by_display_name"),
            approved_at_sq.label("approved_at"),
            latest_comment_sq.label("latest_review_comment"),
        )
        .join(Skill, Skill.id == SkillVersion.skill_id)
        .join(Category, Category.id == Skill.category_id)
        .join(User, User.id == SkillVersion.created_by)
        .where(SkillVersion.review_status == "approved")
        .order_by(approved_at_sq.desc().nullslast(), SkillVersion.created_at.desc())
    )
    return [dict(row) for row in db.execute(query).mappings()]


def get_review_history(db: Session) -> list[dict]:
    query = (
        select(
            SkillVersion.id.label("version_id"),
            Skill.id.label("skill_id"),
            Skill.name.label("skill_name"),
            SkillVersion.version,
            Category.name.label("category_name"),
            VersionReview.action,
            VersionReview.comment,
            User.display_name.label("operator_display_name"),
            VersionReview.created_at,
        )
        .join(SkillVersion, SkillVersion.id == VersionReview.skill_version_id)
        .join(Skill, Skill.id == SkillVersion.skill_id)
        .join(Category, Category.id == Skill.category_id)
        .join(User, User.id == VersionReview.operator_user_id)
        .where(VersionReview.action.in_(["approve", "reject", "publish", "archive", "rollback_publish"]))
        .order_by(VersionReview.created_at.desc())
    )
    return [dict(row) for row in db.execute(query).mappings()]


def get_scope_assignees(db: Session, *, skill_id: str, scope: str, target_type: str) -> list[str]:
    if target_type == "user":
        query = (
            select(User.display_name)
            .join(SkillUserGrant, SkillUserGrant.user_id == User.id)
            .where(SkillUserGrant.skill_id == skill_id, SkillUserGrant.permission_scope == scope)
            .order_by(User.display_name.asc())
        )
    else:
        query = (
            select(Role.name)
            .join(SkillRoleGrant, SkillRoleGrant.role_id == Role.id)
            .where(SkillRoleGrant.skill_id == skill_id, SkillRoleGrant.permission_scope == scope)
            .order_by(Role.name.asc())
        )
    return list(db.execute(query).scalars())


def is_skill_favorited(db: Session, user_id: str, skill_id: str) -> bool:
    return (
        db.execute(
            select(Favorite.user_id).where(Favorite.user_id == user_id, Favorite.skill_id == skill_id)
        ).first()
        is not None
    )


def is_skill_liked(db: Session, user_id: str, skill_id: str) -> bool:
    return (
        db.execute(
            select(SkillLike.user_id).where(SkillLike.user_id == user_id, SkillLike.skill_id == skill_id)
        ).first()
        is not None
    )
