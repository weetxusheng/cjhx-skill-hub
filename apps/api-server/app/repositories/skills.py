from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.department import Department
from app.models.favorite import Favorite
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

"""技能查询仓储层。

约束：
- 仓储层仅负责数据读写与结果整形，不承载权限或状态机判断。
"""


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
    """为前台与后台技能列表应用共享筛选条件（分类 + 关键词）。"""
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
    """统计查询总行数，并移除排序以保证正确性与性能。"""
    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    return db.execute(count_query).scalar_one()


def list_public_skills_paginated(db: Session, params: PublicSkillListParams) -> tuple[list[dict], int]:
    """返回前台技能列表（支持筛选与排序），并返回总数。"""
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
    """返回后台技能分页列表与总数。"""
    return _list_admin_skills(db, params, paginate=True)


def list_admin_skills_all(db: Session, params: AdminSkillListParams) -> list[dict]:
    """返回后台技能全量列表（供 service 层二次过滤）。"""
    items, _ = _list_admin_skills(db, params, paginate=False)
    return items


def list_portal_upload_records_paginated(
    db: Session,
    *,
    user_id: str,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    """返回门户上传中心的当前用户上传记录。"""
    query = (
        select(
            SkillVersion.id.label("version_id"),
            Skill.id.label("skill_id"),
            Skill.name.label("skill_name"),
            Skill.slug.label("skill_slug"),
            Category.name.label("category_name"),
            Category.slug.label("category_slug"),
            SkillVersion.version,
            SkillVersion.review_status,
            SkillVersion.review_comment,
            SkillVersion.published_at,
            SkillVersion.created_at,
            SkillVersion.updated_at,
        )
        .join(Skill, Skill.id == SkillVersion.skill_id)
        .join(Category, Category.id == Skill.category_id)
        .where(SkillVersion.created_by == user_id)
        .order_by(SkillVersion.updated_at.desc(), SkillVersion.created_at.desc())
    )
    total = _count_rows(db, query)
    offset = (page - 1) * page_size
    rows = db.execute(query.offset(offset).limit(page_size)).all()
    items = [
        {
            "version_id": row.version_id,
            "skill_id": row.skill_id,
            "skill_name": row.skill_name,
            "skill_slug": row.skill_slug,
            "category_name": row.category_name,
            "category_slug": row.category_slug,
            "version": row.version,
            "review_status": row.review_status,
            "review_comment": row.review_comment,
            "published_at": row.published_at,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        for row in rows
    ]
    return items, total


def _list_admin_skills(db: Session, params: AdminSkillListParams, *, paginate: bool) -> tuple[list[dict], int]:
    """后台技能列表内部查询构造器（分页与非分页共用）。"""
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
    """按 slug 获取技能详情（仅数据层）。"""
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
    """按 id 获取技能详情（仅数据层）。"""
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
    """返回技能版本摘要；可选仅返回已发布版本。"""
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
    """按版本 id 返回完整详情（含 markdown 与 usage_guide_json）。"""
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
    """返回技能所有版本的审核记录（倒序）。"""
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
    """返回单个版本的审核记录（倒序）。"""
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
    """返回技能的角色授权列表（标准化结构）。"""
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
    return [
        {**dict(row), "target_type": "role", "target_primary_department": None}
        for row in db.execute(query).mappings()
    ]


def get_skill_user_grants(db: Session, skill_id: str) -> list[dict]:
    """返回技能的用户授权列表（标准化结构）。"""
    query = (
        select(
            SkillUserGrant.id,
            SkillUserGrant.user_id.label("target_id"),
            User.display_name.label("target_name"),
            Department.id.label("dept_id"),
            Department.name.label("dept_name"),
            SkillUserGrant.permission_scope,
            SkillUserGrant.created_at,
        )
        .join(User, User.id == SkillUserGrant.user_id)
        .outerjoin(Department, Department.id == User.primary_department_id)
        .where(SkillUserGrant.skill_id == skill_id)
        .order_by(SkillUserGrant.created_at.asc())
    )
    rows: list[dict] = []
    for row in db.execute(query).mappings():
        data = dict(row)
        dept_id = data.pop("dept_id", None)
        dept_name = data.pop("dept_name", None)
        tpd = {"id": dept_id, "name": dept_name} if dept_id else None
        rows.append({**data, "target_type": "user", "target_primary_department": tpd})
    return rows


def get_skill_pending_reviews(db: Session, *, category: str | None = None, created_by: str | None = None) -> list[dict]:
    """返回待审核队列（review_status=submitted）。"""
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
    """返回待发布队列（review_status=approved）。"""
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
    """返回关键流程动作的审核历史（倒序）。"""
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
    """返回指定 skill scope 下已分配用户/角色的展示名。"""
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


def get_scope_assignee_details(db: Session, *, skill_id: str, scope: str) -> list[dict]:
    """返回指定 skill scope 下已分配对象详情；角色项附带当前成员名单。"""
    user_query = (
        select(
            User.id.label("target_id"),
            User.display_name.label("target_name"),
        )
        .join(SkillUserGrant, SkillUserGrant.user_id == User.id)
        .where(SkillUserGrant.skill_id == skill_id, SkillUserGrant.permission_scope == scope)
        .order_by(User.display_name.asc())
    )
    user_items = [
        {
            "target_id": row.target_id,
            "target_type": "user",
            "target_name": row.target_name,
            "members": [],
        }
        for row in db.execute(user_query)
    ]

    role_query = (
        select(
            Role.id.label("target_id"),
            Role.name.label("target_name"),
        )
        .join(SkillRoleGrant, SkillRoleGrant.role_id == Role.id)
        .where(SkillRoleGrant.skill_id == skill_id, SkillRoleGrant.permission_scope == scope)
        .order_by(Role.name.asc())
    )
    role_rows = list(db.execute(role_query))
    role_ids = [row.target_id for row in role_rows]
    role_member_map: dict[UUID, list[str]] = {role_id: [] for role_id in role_ids}
    if role_ids:
        member_rows = db.execute(
            select(UserRole.role_id, User.display_name)
            .join(User, User.id == UserRole.user_id)
            .where(UserRole.role_id.in_(role_ids), User.status == "active")
            .order_by(User.display_name.asc())
        )
        for role_id, display_name in member_rows:
            role_member_map.setdefault(role_id, []).append(display_name)

    role_items = [
        {
            "target_id": row.target_id,
            "target_type": "role",
            "target_name": row.target_name,
            "members": role_member_map.get(row.target_id, []),
        }
        for row in role_rows
    ]
    return [*user_items, *role_items]


def is_skill_favorited(db: Session, user_id: str, skill_id: str) -> bool:
    """判断用户是否已收藏该技能。"""
    return (
        db.execute(
            select(Favorite.user_id).where(Favorite.user_id == user_id, Favorite.skill_id == skill_id)
        ).first()
        is not None
    )


def is_skill_liked(db: Session, user_id: str, skill_id: str) -> bool:
    """判断用户是否已点赞该技能。"""
    return (
        db.execute(
            select(SkillLike.user_id).where(SkillLike.user_id == user_id, SkillLike.skill_id == skill_id)
        ).first()
        is not None
    )
