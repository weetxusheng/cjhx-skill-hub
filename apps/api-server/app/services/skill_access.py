from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.models.role import Role
from app.models.skill_role_grant import SkillRoleGrant
from app.models.skill_user_grant import SkillUserGrant
from app.models.user_role import UserRole

EDIT_SCOPES = {"owner", "maintainer"}
OWNER_SCOPES = {"owner"}
UPLOAD_SCOPES = {"owner", "maintainer"}
SUBMIT_SCOPES = {"owner", "maintainer"}
REVIEW_SCOPES = {"owner", "reviewer"}
PUBLISH_SCOPES = {"owner", "publisher"}
ARCHIVE_SCOPES = {"owner", "publisher"}
ROLLBACK_SCOPES = {"owner", "publisher", "rollback"}
VIEW_SCOPES = {"owner", "maintainer", "reviewer", "publisher", "viewer"}


def is_admin_user(current_user: CurrentUser) -> bool:
    return "admin" in current_user.roles


def get_skill_scopes(db: Session, *, skill_id: UUID, current_user: CurrentUser) -> set[str]:
    scopes = set(
        db.execute(
            select(SkillUserGrant.permission_scope).where(
                SkillUserGrant.skill_id == skill_id,
                SkillUserGrant.user_id == current_user.id,
            )
        ).scalars()
    )
    role_scopes = db.execute(
        select(SkillRoleGrant.permission_scope)
        .join(Role, Role.id == SkillRoleGrant.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(
            SkillRoleGrant.skill_id == skill_id,
            UserRole.user_id == current_user.id,
            Role.is_active.is_(True),
        )
    ).scalars()
    scopes.update(role_scopes)
    return scopes


def skill_has_any_grants(db: Session, *, skill_id: UUID) -> bool:
    role_count = db.execute(select(func.count()).select_from(SkillRoleGrant).where(SkillRoleGrant.skill_id == skill_id)).scalar_one()
    user_count = db.execute(select(func.count()).select_from(SkillUserGrant).where(SkillUserGrant.skill_id == skill_id)).scalar_one()
    return role_count + user_count > 0


def ensure_skill_scopes(db: Session, *, skill_id: UUID, current_user: CurrentUser, allowed_scopes: Iterable[str]) -> None:
    if not has_skill_scope_access(db, skill_id=skill_id, current_user=current_user, allowed_scopes=allowed_scopes):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前账号没有该技能的操作授权")


def has_skill_scope_access(db: Session, *, skill_id: UUID, current_user: CurrentUser, allowed_scopes: Iterable[str]) -> bool:
    if is_admin_user(current_user):
        return True
    if not skill_has_any_grants(db, skill_id=skill_id):
        return True
    scopes = get_skill_scopes(db, skill_id=skill_id, current_user=current_user)
    return bool(set(allowed_scopes).intersection(scopes))
