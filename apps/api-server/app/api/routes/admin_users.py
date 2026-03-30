"""后台用户：分页列表、选项、技能授权视图与启停/角色分配。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_any_permissions, require_permissions
from app.schemas.admin import UserRoleAssignmentRequest
from app.schemas.common import success_response
from app.services.governance import (
    assign_user_roles,
    list_admin_user_options,
    list_admin_users_paginated,
    list_user_skill_grants,
    set_user_status,
)

router = APIRouter()


@router.get("/users")
def list_users(
    q: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions("admin.users.view")),
) -> dict:
    """分页列出用户（关键词与状态筛选）。"""
    payload = list_admin_users_paginated(db, q=q, status_filter=status_filter, page=page, page_size=page_size)
    return success_response(payload.model_dump(mode="json"))


@router.get("/users/options")
def list_user_options(
    q: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_any_permissions("admin.users.view", "skill.edit")),
) -> dict:
    """轻量用户列表，供授权与搜索框使用。"""
    payload = list_admin_user_options(db, q=q, status_filter=status_filter)
    return success_response([item.model_dump(mode="json") for item in payload])


@router.get("/users/{user_id}/skill-grants")
def get_user_skill_grants(
    user_id: UUID,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions("admin.users.view")),
) -> dict:
    """某用户在各技能上的直接/角色继承授权摘要。"""
    payload = list_user_skill_grants(db, user_id=user_id)
    return success_response([item.model_dump(mode="json") for item in payload])


@router.post("/users/{user_id}/roles")
def update_user_roles(
    user_id: UUID,
    payload: UserRoleAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("admin.users.manage")),
) -> dict:
    """覆盖式更新用户全局角色集合。"""
    item = assign_user_roles(db, user_id=user_id, roles=payload.roles, actor_user_id=current_user.id)
    return success_response(item.model_dump(mode="json"))


@router.post("/users/{user_id}/disable")
def disable_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("admin.users.manage")),
) -> dict:
    """禁用用户账号。"""
    item = set_user_status(db, user_id=user_id, enabled=False, actor_user_id=current_user.id)
    return success_response(item.model_dump(mode="json"))


@router.post("/users/{user_id}/enable")
def enable_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("admin.users.manage")),
) -> dict:
    """启用用户账号。"""
    item = set_user_status(db, user_id=user_id, enabled=True, actor_user_id=current_user.id)
    return success_response(item.model_dump(mode="json"))
