from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.skill import Skill
from app.models.skill_version import SkillVersion
from app.models.user import User
from app.models.version_review import VersionReview
from app.schemas.skill import VersionActionResponse
from app.services.audit import write_audit_log
from app.services.cache import delete_cached_json


def _get_version(db: Session, version_id: UUID) -> SkillVersion:
    version = db.execute(select(SkillVersion).where(SkillVersion.id == version_id)).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能版本不存在")
    return version


def _get_skill(db: Session, skill_id: UUID) -> Skill:
    skill = db.execute(select(Skill).where(Skill.id == skill_id)).scalar_one()
    return skill


def _record_review(db: Session, *, version_id: UUID, action: str, comment: str, operator_id: UUID) -> None:
    db.add(
        VersionReview(
            skill_version_id=version_id,
            action=action,
            comment=comment,
            operator_user_id=operator_id,
        )
    )


def _raise_conflict(message: str) -> None:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)


def _sync_skill_fields_from_version(db: Session, *, skill: Skill, version: SkillVersion) -> None:
    manifest = version.manifest_json if isinstance(version.manifest_json, dict) else {}
    name = manifest.get("name")
    summary = manifest.get("summary")
    description = manifest.get("description")
    category_slug = manifest.get("category")

    if isinstance(name, str) and name.strip():
        skill.name = name.strip()
    if isinstance(summary, str) and summary.strip():
        skill.summary = summary.strip()
    if isinstance(description, str) and description.strip():
        skill.description = description.strip()
    if isinstance(category_slug, str) and category_slug.strip():
        category = db.execute(select(Category).where(Category.slug == category_slug.strip())).scalar_one_or_none()
        if category is not None:
            skill.category_id = category.id


def submit_version_for_review(db: Session, *, version_id: UUID, actor: User, comment: str) -> VersionActionResponse:
    version = _get_version(db, version_id)
    if version.review_status not in {"draft", "rejected"}:
        _raise_conflict("当前状态不允许提交审核")
    version.review_status = "submitted"
    version.review_comment = comment or None
    _record_review(db, version_id=version.id, action="submit", comment=comment, operator_id=actor.id)
    write_audit_log(db, actor_user_id=actor.id, action="version.submit", target_type="skill_version", target_id=version.id)
    db.commit()
    delete_cached_json(f"public:skill-detail:{_get_skill(db, version.skill_id).slug}")
    return VersionActionResponse(version_id=version.id, review_status="submitted", message="已提交审核")


def approve_version(db: Session, *, version_id: UUID, actor: User, comment: str) -> VersionActionResponse:
    version = _get_version(db, version_id)
    if version.review_status != "submitted":
        _raise_conflict("只有 submitted 版本可以审核通过")
    version.review_status = "approved"
    version.review_comment = comment or None
    version.reviewed_by = actor.id
    version.reviewed_at = datetime.now(UTC)
    _record_review(db, version_id=version.id, action="approve", comment=comment, operator_id=actor.id)
    write_audit_log(db, actor_user_id=actor.id, action="version.approve", target_type="skill_version", target_id=version.id)
    db.commit()
    delete_cached_json(f"public:skill-detail:{_get_skill(db, version.skill_id).slug}")
    return VersionActionResponse(version_id=version.id, review_status="approved", message="审核通过")


def reject_version(db: Session, *, version_id: UUID, actor: User, comment: str) -> VersionActionResponse:
    if not comment.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="拒绝原因不能为空")
    version = _get_version(db, version_id)
    if version.review_status != "submitted":
        _raise_conflict("只有 submitted 版本可以拒绝")
    version.review_status = "rejected"
    version.review_comment = comment
    version.reviewed_by = actor.id
    version.reviewed_at = datetime.now(UTC)
    _record_review(db, version_id=version.id, action="reject", comment=comment, operator_id=actor.id)
    write_audit_log(db, actor_user_id=actor.id, action="version.reject", target_type="skill_version", target_id=version.id)
    db.commit()
    delete_cached_json(f"public:skill-detail:{_get_skill(db, version.skill_id).slug}")
    return VersionActionResponse(version_id=version.id, review_status="rejected", message="已拒绝该版本")


def publish_version(db: Session, *, version_id: UUID, actor: User, comment: str) -> VersionActionResponse:
    version = _get_version(db, version_id)
    skill = _get_skill(db, version.skill_id)
    if version.review_status != "approved":
        _raise_conflict("只有 approved 版本可以发布")

    now = datetime.now(UTC)
    if skill.current_published_version_id:
        current_version = _get_version(db, skill.current_published_version_id)
        current_version.review_status = "archived"
        _record_review(
            db,
            version_id=current_version.id,
            action="archive",
            comment=f"发布新版本 {version.version} 时自动归档",
            operator_id=actor.id,
        )
        db.flush()

    version.review_status = "published"
    version.published_by = actor.id
    version.published_at = now
    version.review_comment = comment or None
    _sync_skill_fields_from_version(db, skill=skill, version=version)
    skill.current_published_version_id = version.id
    skill.latest_version_no = version.version
    skill.published_at = now

    _record_review(db, version_id=version.id, action="publish", comment=comment, operator_id=actor.id)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="version.publish",
        target_type="skill_version",
        target_id=version.id,
        after_json={"skill_current_published_version_id": str(version.id)},
    )
    db.commit()
    delete_cached_json("public:categories", f"public:skill-detail:{skill.slug}")
    return VersionActionResponse(
        version_id=version.id,
        review_status="published",
        message="版本已发布",
        skill_current_published_version_id=version.id,
    )


def archive_version(db: Session, *, version_id: UUID, actor: User, comment: str) -> VersionActionResponse:
    version = _get_version(db, version_id)
    skill = _get_skill(db, version.skill_id)
    if version.review_status != "published":
        _raise_conflict("只有 published 版本可以归档")
    version.review_status = "archived"
    skill.current_published_version_id = None if skill.current_published_version_id == version.id else skill.current_published_version_id
    if skill.current_published_version_id is None:
        skill.published_at = None
    _record_review(db, version_id=version.id, action="archive", comment=comment, operator_id=actor.id)
    write_audit_log(db, actor_user_id=actor.id, action="version.archive", target_type="skill_version", target_id=version.id)
    db.commit()
    delete_cached_json("public:categories", f"public:skill-detail:{skill.slug}")
    return VersionActionResponse(version_id=version.id, review_status="archived", message="版本已归档")


def rollback_version(db: Session, *, version_id: UUID, actor: User, comment: str) -> VersionActionResponse:
    if not comment.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="回滚说明不能为空")
    version = _get_version(db, version_id)
    skill = _get_skill(db, version.skill_id)
    if version.review_status != "archived":
        _raise_conflict("只有 archived 版本可以回滚发布")

    now = datetime.now(UTC)
    if skill.current_published_version_id:
        current_version = _get_version(db, skill.current_published_version_id)
        current_version.review_status = "archived"
        _record_review(db, version_id=current_version.id, action="archive", comment="回滚时自动归档", operator_id=actor.id)
        db.flush()

    version.review_status = "published"
    version.published_by = actor.id
    version.published_at = now
    version.review_comment = comment
    _sync_skill_fields_from_version(db, skill=skill, version=version)
    skill.current_published_version_id = version.id
    skill.latest_version_no = version.version
    skill.published_at = now

    _record_review(db, version_id=version.id, action="rollback_publish", comment=comment, operator_id=actor.id)
    write_audit_log(
        db,
        actor_user_id=actor.id,
        action="version.rollback",
        target_type="skill_version",
        target_id=version.id,
        after_json={"skill_current_published_version_id": str(version.id)},
    )
    db.commit()
    delete_cached_json("public:categories", f"public:skill-detail:{skill.slug}")
    return VersionActionResponse(
        version_id=version.id,
        review_status="published",
        message="已回滚发布该版本",
        skill_current_published_version_id=version.id,
    )
