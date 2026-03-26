from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_permissions
from app.models.user import User
from app.models.skill_version import SkillVersion
from app.schemas.common import success_response
from app.schemas.skill import UpdateVersionRequest, VersionActionRequest
from app.services.skill_access import ARCHIVE_SCOPES, PUBLISH_SCOPES, REVIEW_SCOPES, ROLLBACK_SCOPES, SUBMIT_SCOPES, VIEW_SCOPES, ensure_skill_scopes
from app.services.skill_lifecycle import (
    approve_version,
    archive_version,
    publish_version,
    reject_version,
    rollback_version,
    submit_version_for_review,
)
from app.services.skills import get_admin_version_detail, update_version_content

router = APIRouter()


def _skill_id_for_version(db: Session, version_id: UUID) -> UUID:
    version = db.get(SkillVersion, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能版本不存在")
    return version.skill_id


@router.get("/versions/{version_id}")
def get_version_detail(
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.view")),
) -> dict:
    ensure_skill_scopes(db, skill_id=_skill_id_for_version(db, version_id), current_user=current_user, allowed_scopes=VIEW_SCOPES)
    payload = get_admin_version_detail(db, version_id, current_user)
    return success_response(payload.model_dump(mode="json"))


@router.patch("/versions/{version_id}")
def patch_version(
    version_id: UUID,
    body: UpdateVersionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.version.edit")),
) -> dict:
    ensure_skill_scopes(db, skill_id=_skill_id_for_version(db, version_id), current_user=current_user, allowed_scopes={"owner", "maintainer"})
    payload = update_version_content(
        db,
        version_id=version_id,
        changelog=body.changelog,
        install_notes=body.install_notes,
        breaking_changes=body.breaking_changes,
        readme_markdown=body.readme_markdown,
        usage_guide_json=body.usage_guide_json.model_dump(mode="python"),
    )
    return success_response(payload.model_dump(mode="json"))


@router.post("/versions/{version_id}/submit")
def submit_version(
    version_id: UUID,
    body: VersionActionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.submit")),
) -> dict:
    ensure_skill_scopes(db, skill_id=_skill_id_for_version(db, version_id), current_user=current_user, allowed_scopes=SUBMIT_SCOPES)
    actor = db.get(User, current_user.id)
    assert actor is not None
    payload = submit_version_for_review(db, version_id=version_id, actor=actor, comment=body.comment)
    return success_response(payload.model_dump(mode="json"))


@router.post("/versions/{version_id}/approve")
def approve(
    version_id: UUID,
    body: VersionActionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.review")),
) -> dict:
    ensure_skill_scopes(db, skill_id=_skill_id_for_version(db, version_id), current_user=current_user, allowed_scopes=REVIEW_SCOPES)
    actor = db.get(User, current_user.id)
    assert actor is not None
    payload = approve_version(db, version_id=version_id, actor=actor, comment=body.comment)
    return success_response(payload.model_dump(mode="json"))


@router.post("/versions/{version_id}/reject")
def reject(
    version_id: UUID,
    body: VersionActionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.review")),
) -> dict:
    ensure_skill_scopes(db, skill_id=_skill_id_for_version(db, version_id), current_user=current_user, allowed_scopes=REVIEW_SCOPES)
    actor = db.get(User, current_user.id)
    assert actor is not None
    payload = reject_version(db, version_id=version_id, actor=actor, comment=body.comment)
    return success_response(payload.model_dump(mode="json"))


@router.post("/versions/{version_id}/publish")
def publish(
    version_id: UUID,
    body: VersionActionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.publish")),
) -> dict:
    ensure_skill_scopes(db, skill_id=_skill_id_for_version(db, version_id), current_user=current_user, allowed_scopes=PUBLISH_SCOPES)
    actor = db.get(User, current_user.id)
    assert actor is not None
    payload = publish_version(db, version_id=version_id, actor=actor, comment=body.comment)
    return success_response(payload.model_dump(mode="json"))


@router.post("/versions/{version_id}/archive")
def archive(
    version_id: UUID,
    body: VersionActionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.archive")),
) -> dict:
    ensure_skill_scopes(db, skill_id=_skill_id_for_version(db, version_id), current_user=current_user, allowed_scopes=ARCHIVE_SCOPES)
    actor = db.get(User, current_user.id)
    assert actor is not None
    payload = archive_version(db, version_id=version_id, actor=actor, comment=body.comment)
    return success_response(payload.model_dump(mode="json"))


@router.post("/versions/{version_id}/rollback")
def rollback(
    version_id: UUID,
    body: VersionActionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("skill.rollback")),
) -> dict:
    ensure_skill_scopes(db, skill_id=_skill_id_for_version(db, version_id), current_user=current_user, allowed_scopes=ROLLBACK_SCOPES)
    actor = db.get(User, current_user.id)
    assert actor is not None
    payload = rollback_version(db, version_id=version_id, actor=actor, comment=body.comment)
    return success_response(payload.model_dump(mode="json"))
