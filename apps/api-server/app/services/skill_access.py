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

"""技能级授权辅助函数。

关键约束：
- 权限校验是两层模型：全局权限决定是否可访问某类页面/API，skill 级授权决定是否可访问某个具体 skill。
- 当 skill 未配置任何授权记录时，对非管理员按“默认可访问”处理。

参考：
- docs/10-architecture/data-and-permissions.md
- docs/30-product-flows/skill-authorization-and-metrics.md
"""

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
    """判断用户是否具备全局 admin 角色。

    说明：
    - 在 `has_skill_scope_access` 中，admin 角色可绕过 skill 级授权。
    """
    return "admin" in current_user.roles


def get_skill_scopes(db: Session, *, skill_id: UUID, current_user: CurrentUser) -> set[str]:
    """汇总用户在指定 skill 上的有效 scope。

    包含：
    - 用户直授（`SkillUserGrant`）
    - 通过激活角色继承的授权（`SkillRoleGrant` + `UserRole` + `Role.is_active`）
    """
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
    """判断某个 skill 是否配置过任意用户/角色授权。"""
    role_count = db.execute(select(func.count()).select_from(SkillRoleGrant).where(SkillRoleGrant.skill_id == skill_id)).scalar_one()
    user_count = db.execute(select(func.count()).select_from(SkillUserGrant).where(SkillUserGrant.skill_id == skill_id)).scalar_one()
    return role_count + user_count > 0


def ensure_skill_scopes(db: Session, *, skill_id: UUID, current_user: CurrentUser, allowed_scopes: Iterable[str]) -> None:
    """当用户不具备允许的 skill scope 时抛出 HTTP 403。"""
    if not has_skill_scope_access(db, skill_id=skill_id, current_user=current_user, allowed_scopes=allowed_scopes):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前账号没有该技能的操作授权")


def has_skill_scope_access(db: Session, *, skill_id: UUID, current_user: CurrentUser, allowed_scopes: Iterable[str]) -> bool:
    """判断用户是否在指定 skill 上具备任一允许 scope。

    边界：
    - admin 可绕过 skill 级授权校验。
    - 若 skill 未配置任何授权，按默认可访问处理。
    """
    if is_admin_user(current_user):
        return True
    if not skill_has_any_grants(db, skill_id=skill_id):
        return True
    scopes = get_skill_scopes(db, skill_id=skill_id, current_user=current_user)
    return bool(set(allowed_scopes).intersection(scopes))
