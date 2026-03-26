from __future__ import annotations

from pathlib import Path
import ipaddress
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import delete, desc, func, or_, select, update
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.core.config import get_settings
from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.download_log import DownloadLog
from app.models.favorite import Favorite
from app.models.file_asset import FileAsset
from app.models.role import Role
from app.models.skill import Skill
from app.models.skill_like import SkillLike
from app.models.skill_role_grant import SkillRoleGrant
from app.models.skill_user_grant import SkillUserGrant
from app.models.skill_version import SkillVersion
from app.models.user import User
from app.models.user_role import UserRole
from app.models.version_review import VersionReview
from app.repositories.skills import (
    AdminSkillListParams,
    PublicSkillListParams,
    get_review_records_for_skill,
    get_review_records_for_version,
    get_review_history,
    get_scope_assignees,
    get_skill_detail_by_id,
    get_skill_detail_by_slug,
    get_skill_pending_releases,
    get_skill_pending_reviews,
    get_skill_role_grants,
    get_skill_user_grants,
    get_version_detail,
    is_skill_liked,
    get_version_summaries_for_skill,
    is_skill_favorited,
    list_admin_skills_all,
    list_admin_skills_paginated,
    list_public_skills_paginated,
)
from app.schemas.admin import (
    AdminAuditLogItem,
    AdminReviewListItem,
    AdminUserListItem,
    PendingReleaseItem,
    ReviewHistoryItem,
    SkillDownloadRecord,
    SkillFavoriteRecord,
    SkillGrantItem,
    SkillStatsOverview,
    SkillStatsSeriesPoint,
)
from app.schemas.common import PagedResponse
from app.schemas.skill import (
    AdminSkillDetailResponse,
    AdminSkillListItem,
    AdminVersionDetail,
    AdminVersionDetailResponse,
    AdminVersionSkillSummary,
    DownloadResponse,
    FavoriteResponse,
    LikeResponse,
    PublicSkillCurrentVersion,
    PublicSkillDetailResponse,
    PublicSkillListItem,
    ReviewRecordItem,
    SkillDetailBase,
    SkillVersionSummary,
    UsageGuide,
)
from app.services.markdown import render_markdown_html
from app.services.cache import delete_cached_json, get_cached_json, set_cached_json
from app.services.audit import write_audit_log
from app.services.skill_access import (
    ARCHIVE_SCOPES,
    EDIT_SCOPES,
    OWNER_SCOPES,
    PUBLISH_SCOPES,
    REVIEW_SCOPES,
    ROLLBACK_SCOPES,
    SUBMIT_SCOPES,
    UPLOAD_SCOPES,
    VIEW_SCOPES,
    has_skill_scope_access,
    is_admin_user,
)
from app.services.storage import build_download_response
from app.services.usage_guides import normalize_usage_guide

settings = get_settings()


def _has_permission(current_user: CurrentUser, permission: str) -> bool:
    return permission in current_user.permissions


def _can_access_skill(
    db: Session,
    *,
    skill_id: UUID,
    current_user: CurrentUser,
    permission: str,
    allowed_scopes: set[str],
) -> bool:
    return _has_permission(current_user, permission) and has_skill_scope_access(
        db,
        skill_id=skill_id,
        current_user=current_user,
        allowed_scopes=allowed_scopes,
    )


def _build_skill_capabilities(db: Session, *, skill_id: UUID, current_user: CurrentUser):
    can_view_details = _can_access_skill(
        db,
        skill_id=skill_id,
        current_user=current_user,
        permission="admin.users.view",
        allowed_scopes=VIEW_SCOPES,
    )
    return {
        "edit_skill": _can_access_skill(
            db,
            skill_id=skill_id,
            current_user=current_user,
            permission="skill.edit",
            allowed_scopes=EDIT_SCOPES,
        ),
        "upload_version": _can_access_skill(
            db,
            skill_id=skill_id,
            current_user=current_user,
            permission="skill.upload",
            allowed_scopes=UPLOAD_SCOPES,
        ),
        "manage_grants": _can_access_skill(
            db,
            skill_id=skill_id,
            current_user=current_user,
            permission="skill.edit",
            allowed_scopes=OWNER_SCOPES,
        ),
        "view_favorite_details": can_view_details,
        "view_download_details": can_view_details,
        "view_sensitive_download_details": can_view_details and is_admin_user(current_user),
    }


def _build_version_capabilities(db: Session, *, skill_id: UUID, current_user: CurrentUser, review_status: str):
    return {
        "edit_content": review_status in {"draft", "rejected"}
        and _can_access_skill(
            db,
            skill_id=skill_id,
            current_user=current_user,
            permission="skill.version.edit",
            allowed_scopes=EDIT_SCOPES,
        ),
        "submit": review_status in {"draft", "rejected"}
        and _can_access_skill(
            db,
            skill_id=skill_id,
            current_user=current_user,
            permission="skill.submit",
            allowed_scopes=SUBMIT_SCOPES,
        ),
        "approve": review_status == "submitted"
        and _can_access_skill(
            db,
            skill_id=skill_id,
            current_user=current_user,
            permission="skill.review",
            allowed_scopes=REVIEW_SCOPES,
        ),
        "reject": review_status == "submitted"
        and _can_access_skill(
            db,
            skill_id=skill_id,
            current_user=current_user,
            permission="skill.review",
            allowed_scopes=REVIEW_SCOPES,
        ),
        "publish": review_status == "approved"
        and _can_access_skill(
            db,
            skill_id=skill_id,
            current_user=current_user,
            permission="skill.publish",
            allowed_scopes=PUBLISH_SCOPES,
        ),
        "archive": review_status == "published"
        and _can_access_skill(
            db,
            skill_id=skill_id,
            current_user=current_user,
            permission="skill.archive",
            allowed_scopes=ARCHIVE_SCOPES,
        ),
        "rollback": review_status == "archived"
        and _can_access_skill(
            db,
            skill_id=skill_id,
            current_user=current_user,
            permission="skill.rollback",
            allowed_scopes=ROLLBACK_SCOPES,
        ),
    }


def get_public_skill_list(db: Session, params: PublicSkillListParams) -> PagedResponse[PublicSkillListItem]:
    items, total = list_public_skills_paginated(db, params)
    return PagedResponse[PublicSkillListItem](
        items=[PublicSkillListItem.model_validate(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


def get_admin_skill_list(db: Session, params: AdminSkillListParams, current_user: CurrentUser) -> PagedResponse[AdminSkillListItem]:
    if "admin" in current_user.roles:
        items, total = list_admin_skills_paginated(db, params)
    else:
        all_items = list_admin_skills_all(db, params)
        filtered_items = [
            item
            for item in all_items
            if has_skill_scope_access(db, skill_id=item["id"], current_user=current_user, allowed_scopes=VIEW_SCOPES)
        ]
        total = len(filtered_items)
        offset = (params.page - 1) * params.page_size
        items = filtered_items[offset : offset + params.page_size]
    return PagedResponse[AdminSkillListItem](
        items=[AdminSkillListItem.model_validate(item) for item in items],
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


def get_public_skill_detail(db: Session, slug: str, current_user: CurrentUser | None) -> PublicSkillDetailResponse:
    cache_key = f"public:skill-detail:{slug}"
    cached = get_cached_json(cache_key)
    if cached is not None:
        payload = PublicSkillDetailResponse.model_validate(cached)
        if current_user is not None:
            payload.is_favorited = is_skill_favorited(db, str(current_user.id), str(payload.skill.id))
            payload.is_liked = is_skill_liked(db, str(current_user.id), str(payload.skill.id))
        return payload

    detail = get_skill_detail_by_slug(db, slug)
    if detail is None or detail["current_published_version_id"] is None or detail["status"] != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在或未发布")

    current_version = get_version_detail(db, detail["current_published_version_id"])
    if current_version is None or current_version["review_status"] != "published":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在或未发布")

    is_favorited = False
    is_liked = False
    if current_user is not None:
        is_favorited = is_skill_favorited(db, str(current_user.id), str(detail["id"]))
        is_liked = is_skill_liked(db, str(current_user.id), str(detail["id"]))

    version_summaries = [
        SkillVersionSummary.model_validate(item)
        for item in get_version_summaries_for_skill(db, str(detail["id"]), only_published=True)
    ]
    usage_guide = UsageGuide.model_validate(
        normalize_usage_guide(
            current_version.get("usage_guide_json"),
            skill_id=detail["id"],
            skill_name=detail["name"],
            skill_slug=detail["slug"],
            summary=detail["summary"],
            description=detail["description"],
            install_notes=current_version["install_notes"],
        )
    )
    payload = PublicSkillDetailResponse(
        skill=SkillDetailBase.model_validate(detail),
        current_version=PublicSkillCurrentVersion(
            id=current_version["id"],
            version=current_version["version"],
            readme_markdown=current_version["readme_markdown"],
            readme_html=render_markdown_html(current_version["readme_markdown"]),
            changelog=current_version["changelog"],
            install_notes=current_version["install_notes"],
            breaking_changes=current_version["breaking_changes"],
            published_at=current_version["published_at"],
        ),
        published_versions=version_summaries,
        is_favorited=is_favorited,
        is_liked=is_liked,
        usage_guide=usage_guide,
    )
    set_cached_json(
        cache_key,
        {**payload.model_dump(mode="json"), "is_favorited": False, "is_liked": False},
        settings.skill_detail_cache_ttl_seconds,
    )
    return payload


def get_admin_skill_detail(db: Session, skill_id: UUID, current_user: CurrentUser) -> AdminSkillDetailResponse:
    detail = get_skill_detail_by_id(db, str(skill_id))
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")

    versions = [SkillVersionSummary.model_validate(item) for item in get_version_summaries_for_skill(db, str(skill_id))]
    reviews = [ReviewRecordItem.model_validate(item) for item in get_review_records_for_skill(db, str(skill_id))]
    latest_version_status = versions[0].review_status if versions else None
    current_published_version = next((item.version for item in versions if item.id == detail["current_published_version_id"]), None)
    pending_review_count = sum(1 for item in versions if item.review_status == "submitted")
    pending_release_count = sum(1 for item in versions if item.review_status == "approved")
    owner = db.get(User, detail["owner_user_id"]) if detail.get("owner_user_id") else None
    return AdminSkillDetailResponse(
        skill=SkillDetailBase.model_validate({**detail, "owner_display_name": owner.display_name if owner else None}),
        versions=versions,
        recent_reviews=reviews[:20],
        latest_version_status=latest_version_status,
        current_published_version=current_published_version,
        pending_review_count=pending_review_count,
        pending_release_count=pending_release_count,
        capabilities=_build_skill_capabilities(db, skill_id=skill_id, current_user=current_user),
    )


def get_admin_version_detail(db: Session, version_id: UUID, current_user: CurrentUser) -> AdminVersionDetailResponse:
    version = get_version_detail(db, str(version_id))
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能版本不存在")
    skill = get_skill_detail_by_id(db, str(version["skill_id"]))
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    reviews = [ReviewRecordItem.model_validate(item) for item in get_review_records_for_version(db, str(version_id))]
    version_payload = {**version}
    version_payload.pop("usage_guide_json", None)
    return AdminVersionDetailResponse(
        skill=AdminVersionSkillSummary(
            id=skill["id"],
            name=skill["name"],
            slug=skill["slug"],
            category_name=skill["category_name"],
            category_slug=skill["category_slug"],
            current_published_version_id=skill["current_published_version_id"],
        ),
        version=AdminVersionDetail(
            **version_payload,
            usage_guide_json=UsageGuide.model_validate(
                normalize_usage_guide(
                    version.get("usage_guide_json"),
                    skill_id=skill["id"],
                    skill_name=skill["name"],
                    skill_slug=skill["slug"],
                    summary=skill["summary"],
                    description=skill["description"],
                    install_notes=version["install_notes"],
                )
            ),
            readme_html=render_markdown_html(version["readme_markdown"]),
        ),
        reviews=reviews,
        capabilities=_build_version_capabilities(
            db,
            skill_id=skill["id"],
            current_user=current_user,
            review_status=version["review_status"],
        ),
    )


def update_skill_display(
    db: Session,
    *,
    skill_id: UUID,
    name: str,
    summary: str,
    description: str,
    category_slug: str,
) -> SkillDetailBase:
    skill = db.execute(select(Skill).where(Skill.id == skill_id)).scalar_one_or_none()
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    category = db.execute(select(Category).where(Category.slug == category_slug)).scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类 slug 不存在")
    skill.name = name
    skill.summary = summary
    skill.description = description
    skill.category_id = category.id
    db.commit()
    delete_cached_json("public:categories", f"public:skill-detail:{skill.slug}")
    updated = get_skill_detail_by_id(db, str(skill_id))
    assert updated is not None
    return SkillDetailBase.model_validate(updated)


def update_version_content(
    db: Session,
    *,
    version_id: UUID,
    changelog: str,
    install_notes: str,
    breaking_changes: str,
    readme_markdown: str,
    usage_guide_json: dict,
) -> AdminVersionDetail:
    version = db.execute(select(SkillVersion).where(SkillVersion.id == version_id)).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能版本不存在")
    if version.review_status not in {"draft", "rejected"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前状态不允许编辑版本文案")
    version.changelog = changelog
    version.install_notes = install_notes
    version.breaking_changes = breaking_changes
    version.readme_markdown = readme_markdown
    version.usage_guide_json = usage_guide_json
    db.commit()
    payload = get_version_detail(db, str(version_id))
    assert payload is not None
    skill = get_skill_detail_by_id(db, str(payload["skill_id"]))
    assert skill is not None
    version_payload = {**payload}
    version_payload.pop("usage_guide_json", None)
    return AdminVersionDetail(
        **version_payload,
        usage_guide_json=UsageGuide.model_validate(
            normalize_usage_guide(
                payload.get("usage_guide_json"),
                skill_id=skill["id"],
                skill_name=skill["name"],
                skill_slug=skill["slug"],
                summary=skill["summary"],
                description=skill["description"],
                install_notes=payload["install_notes"],
            )
        ),
        readme_html=render_markdown_html(payload["readme_markdown"]),
    )


def toggle_favorite(db: Session, *, skill_id: UUID, user: CurrentUser, favorited: bool) -> FavoriteResponse:
    skill = db.execute(select(Skill).where(Skill.id == skill_id)).scalar_one_or_none()
    if skill is None or skill.current_published_version_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在或未发布")
    existing = db.execute(
        select(Favorite).where(Favorite.skill_id == skill_id, Favorite.user_id == user.id)
    ).scalar_one_or_none()
    if favorited and existing is None:
        db.add(Favorite(user_id=user.id, skill_id=skill_id))
        skill.favorite_count += 1
    if not favorited and existing is not None:
        db.delete(existing)
        skill.favorite_count = max(skill.favorite_count - 1, 0)
    db.commit()
    db.refresh(skill)
    delete_cached_json(f"public:skill-detail:{skill.slug}")
    return FavoriteResponse(favorited=favorited and existing is None or favorited and existing is not None, favorite_count=skill.favorite_count)


def toggle_like(db: Session, *, skill_id: UUID, user: CurrentUser, liked: bool) -> LikeResponse:
    skill = db.execute(select(Skill).where(Skill.id == skill_id)).scalar_one_or_none()
    if skill is None or skill.current_published_version_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在或未发布")
    existing = db.execute(
        select(SkillLike).where(SkillLike.skill_id == skill_id, SkillLike.user_id == user.id)
    ).scalar_one_or_none()
    if liked and existing is None:
        db.add(SkillLike(user_id=user.id, skill_id=skill_id))
        skill.like_count += 1
    if not liked and existing is not None:
        db.delete(existing)
        skill.like_count = max(skill.like_count - 1, 0)
    db.commit()
    db.refresh(skill)
    delete_cached_json(f"public:skill-detail:{skill.slug}")
    return LikeResponse(liked=liked, like_count=skill.like_count)


def download_skill_package(
    db: Session,
    *,
    skill_id: UUID,
    current_user: CurrentUser | None,
    request: Request,
):
    skill = db.execute(select(Skill).where(Skill.id == skill_id)).scalar_one_or_none()
    if skill is None or skill.current_published_version_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在或未发布")
    version = db.execute(select(SkillVersion).where(SkillVersion.id == skill.current_published_version_id)).scalar_one()
    asset = db.execute(select(FileAsset).where(FileAsset.id == version.package_file_id)).scalar_one()
    client_ip = request.client.host if request.client else None
    try:
        ipaddress.ip_address(client_ip) if client_ip else None
    except ValueError:
        client_ip = None

    db.add(
        DownloadLog(
            skill_id=skill.id,
            skill_version_id=version.id,
            user_id=current_user.id if current_user else None,
            ip=client_ip,
            user_agent=request.headers.get("user-agent"),
        )
    )
    skill.download_count += 1
    db.commit()
    response = DownloadResponse(downloaded=True, download_count=skill.download_count, filename=asset.original_name)
    return build_download_response(object_key=asset.object_key, original_name=asset.original_name, mime_type=asset.mime_type), response


def get_review_queue(
    db: Session,
    *,
    category: str | None = None,
    created_by: str | None = None,
    current_user: CurrentUser,
) -> list[AdminReviewListItem]:
    rows = get_skill_pending_reviews(db, category=category, created_by=created_by)
    return [
        AdminReviewListItem.model_validate(
            {
                **row,
                "assigned_reviewers": get_scope_assignees(db, skill_id=str(row["skill_id"]), scope="reviewer", target_type="user")
                + get_scope_assignees(db, skill_id=str(row["skill_id"]), scope="reviewer", target_type="role"),
                "assigned_publishers": get_scope_assignees(db, skill_id=str(row["skill_id"]), scope="publisher", target_type="user")
                + get_scope_assignees(db, skill_id=str(row["skill_id"]), scope="publisher", target_type="role"),
            }
        )
        for row in rows
        if has_skill_scope_access(db, skill_id=row["skill_id"], current_user=current_user, allowed_scopes=REVIEW_SCOPES)
    ]


def get_pending_releases(db: Session, *, current_user: CurrentUser) -> list[PendingReleaseItem]:
    rows = get_skill_pending_releases(db)
    return [
        PendingReleaseItem.model_validate(
            {
                **row,
                "assigned_publishers": get_scope_assignees(db, skill_id=str(row["skill_id"]), scope="publisher", target_type="user")
                + get_scope_assignees(db, skill_id=str(row["skill_id"]), scope="publisher", target_type="role"),
            }
        )
        for row in rows
        if has_skill_scope_access(db, skill_id=row["skill_id"], current_user=current_user, allowed_scopes=PUBLISH_SCOPES)
    ]


def get_review_history_feed(db: Session, *, current_user: CurrentUser) -> list[ReviewHistoryItem]:
    return [
        ReviewHistoryItem.model_validate(row)
        for row in get_review_history(db)
        if has_skill_scope_access(db, skill_id=row["skill_id"], current_user=current_user, allowed_scopes=VIEW_SCOPES)
    ]


def get_skill_permissions_payload(db: Session, *, skill_id: UUID) -> list[SkillGrantItem]:
    role_grants = [SkillGrantItem.model_validate(item) for item in get_skill_role_grants(db, str(skill_id))]
    user_grants = [SkillGrantItem.model_validate(item) for item in get_skill_user_grants(db, str(skill_id))]
    return sorted([*role_grants, *user_grants], key=lambda item: (item.permission_scope, item.target_type, item.target_name))


def assign_skill_role_grants(
    db: Session,
    *,
    skill_id: UUID,
    role_ids: list[UUID],
    permission_scope: str,
    actor_user_id: UUID,
) -> list[SkillGrantItem]:
    for role_id in role_ids:
        exists = db.execute(
            select(SkillRoleGrant).where(
                SkillRoleGrant.skill_id == skill_id,
                SkillRoleGrant.role_id == role_id,
                SkillRoleGrant.permission_scope == permission_scope,
            )
        ).scalar_one_or_none()
        if exists is None:
            db.add(SkillRoleGrant(skill_id=skill_id, role_id=role_id, permission_scope=permission_scope))
    write_audit_log(
        db,
        actor_user_id=actor_user_id,
        action="skill.grants.roles.assign",
        target_type="skill",
        target_id=skill_id,
        after_json={"role_ids": [str(item) for item in role_ids], "permission_scope": permission_scope},
    )
    db.commit()
    return get_skill_permissions_payload(db, skill_id=skill_id)


def assign_skill_user_grants(
    db: Session,
    *,
    skill_id: UUID,
    user_ids: list[UUID],
    permission_scope: str,
    actor_user_id: UUID,
) -> list[SkillGrantItem]:
    for user_id in user_ids:
        exists = db.execute(
            select(SkillUserGrant).where(
                SkillUserGrant.skill_id == skill_id,
                SkillUserGrant.user_id == user_id,
                SkillUserGrant.permission_scope == permission_scope,
            )
        ).scalar_one_or_none()
        if exists is None:
            db.add(SkillUserGrant(skill_id=skill_id, user_id=user_id, permission_scope=permission_scope))
    write_audit_log(
        db,
        actor_user_id=actor_user_id,
        action="skill.grants.users.assign",
        target_type="skill",
        target_id=skill_id,
        after_json={"user_ids": [str(item) for item in user_ids], "permission_scope": permission_scope},
    )
    db.commit()
    return get_skill_permissions_payload(db, skill_id=skill_id)


def delete_skill_role_grant(db: Session, *, skill_id: UUID, grant_id: UUID, actor_user_id: UUID) -> None:
    grant = db.execute(select(SkillRoleGrant).where(SkillRoleGrant.id == grant_id, SkillRoleGrant.skill_id == skill_id)).scalar_one_or_none()
    if grant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色授权不存在")
    db.delete(grant)
    write_audit_log(db, actor_user_id=actor_user_id, action="skill.grants.roles.delete", target_type="skill", target_id=skill_id)
    db.commit()


def delete_skill_user_grant(db: Session, *, skill_id: UUID, grant_id: UUID, actor_user_id: UUID) -> None:
    grant = db.execute(select(SkillUserGrant).where(SkillUserGrant.id == grant_id, SkillUserGrant.skill_id == skill_id)).scalar_one_or_none()
    if grant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户授权不存在")
    db.delete(grant)
    write_audit_log(db, actor_user_id=actor_user_id, action="skill.grants.users.delete", target_type="skill", target_id=skill_id)
    db.commit()


def _build_daily_series(rows: list[dict]) -> list[SkillStatsSeriesPoint]:
    return [SkillStatsSeriesPoint(day=str(row["day"]), count=row["count"]) for row in rows]


def get_skill_stats(db: Session, *, skill_id: UUID) -> SkillStatsOverview:
    skill = db.execute(select(Skill).where(Skill.id == skill_id)).scalar_one_or_none()
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
    recent_downloads = db.execute(
        select(func.date(DownloadLog.created_at).label("day"), func.count().label("count"))
        .where(DownloadLog.skill_id == skill_id)
        .group_by(func.date(DownloadLog.created_at))
        .order_by(func.date(DownloadLog.created_at).desc())
        .limit(30)
    ).mappings().all()
    recent_favorites = db.execute(
        select(func.date(Favorite.created_at).label("day"), func.count().label("count"))
        .where(Favorite.skill_id == skill_id)
        .group_by(func.date(Favorite.created_at))
        .order_by(func.date(Favorite.created_at).desc())
        .limit(30)
    ).mappings().all()
    recent_likes = db.execute(
        select(func.date(SkillLike.created_at).label("day"), func.count().label("count"))
        .where(SkillLike.skill_id == skill_id)
        .group_by(func.date(SkillLike.created_at))
        .order_by(func.date(SkillLike.created_at).desc())
        .limit(30)
    ).mappings().all()
    return SkillStatsOverview(
        skill_id=skill.id,
        like_count=skill.like_count,
        favorite_count=skill.favorite_count,
        download_count=skill.download_count,
        recent_downloads=_build_daily_series(recent_downloads),
        recent_favorites=_build_daily_series(recent_favorites),
        recent_likes=_build_daily_series(recent_likes),
    )


def get_skill_favorite_records(db: Session, *, skill_id: UUID) -> list[SkillFavoriteRecord]:
    rows = db.execute(
        select(Favorite.user_id, User.username, User.display_name, Favorite.created_at)
        .join(User, User.id == Favorite.user_id)
        .where(Favorite.skill_id == skill_id)
        .order_by(Favorite.created_at.desc())
    ).mappings()
    return [SkillFavoriteRecord.model_validate(row) for row in rows]


def get_skill_download_records(db: Session, *, skill_id: UUID, current_user: CurrentUser) -> list[SkillDownloadRecord]:
    show_sensitive = is_admin_user(current_user)
    rows = db.execute(
        select(
            DownloadLog.id,
            DownloadLog.user_id,
            User.username,
            User.display_name,
            SkillVersion.version,
            DownloadLog.created_at,
            DownloadLog.ip,
            DownloadLog.user_agent,
        )
        .join(SkillVersion, SkillVersion.id == DownloadLog.skill_version_id)
        .outerjoin(User, User.id == DownloadLog.user_id)
        .where(DownloadLog.skill_id == skill_id)
        .order_by(DownloadLog.created_at.desc())
    ).mappings()
    payload: list[SkillDownloadRecord] = []
    for row in rows:
        data = dict(row)
        if data["ip"] is not None:
            data["ip"] = str(data["ip"])
        if not show_sensitive:
            data["ip"] = None
            data["user_agent"] = None
            if data["user_id"] is None:
                data["username"] = None
                data["display_name"] = None
        payload.append(SkillDownloadRecord.model_validate(data))
    return payload


def get_admin_users(db: Session) -> list[AdminUserListItem]:
    users = list(db.execute(select(User).order_by(User.created_at.desc())).scalars())
    role_map: dict[UUID, list[str]] = {user.id: [] for user in users}
    rows = db.execute(
        select(UserRole.user_id, Role.code)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id.in_(list(role_map.keys()) or [UUID(int=0)]))
    ).all()
    for user_id, role_code in rows:
        role_map[user_id].append(role_code)
    return [
        AdminUserListItem(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            email=user.email,
            status=user.status,
            roles=sorted(role_map.get(user.id, [])),
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )
        for user in users
    ]


def get_admin_audit_logs(db: Session, limit: int = 100) -> list[AdminAuditLogItem]:
    query = (
        select(
            AuditLog.id,
            AuditLog.actor_user_id,
            User.display_name.label("actor_display_name"),
            AuditLog.action,
            AuditLog.target_type,
            AuditLog.target_id,
            AuditLog.created_at,
        )
        .outerjoin(User, User.id == AuditLog.actor_user_id)
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
    )
    return [AdminAuditLogItem.model_validate(row) for row in db.execute(query).mappings()]
