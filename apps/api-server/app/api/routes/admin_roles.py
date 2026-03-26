from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fastapi import Query

from app.api.deps import CurrentUser, get_db, require_any_permissions, require_permissions
from app.schemas.admin import RolePermissionsRequest, RoleUpsertRequest
from app.schemas.common import success_response
from app.services.governance import (
    create_role,
    list_permissions,
    list_role_options,
    list_roles_paginated,
    set_role_permissions,
    set_role_status,
    update_role,
)

router = APIRouter()


@router.get("/permissions")
def get_permissions(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions("admin.roles.view")),
) -> dict:
    items = [item.model_dump(mode="json") for item in list_permissions(db)]
    return success_response(items)


@router.get("/roles")
def get_roles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions("admin.roles.view")),
) -> dict:
    payload = list_roles_paginated(db, page=page, page_size=page_size)
    return success_response(payload.model_dump(mode="json"))


@router.get("/roles/options")
def get_role_options(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_any_permissions("admin.roles.view", "skill.edit")),
) -> dict:
    items = [item.model_dump(mode="json") for item in list_role_options(db)]
    return success_response(items)


@router.post("/roles")
def post_role(
    payload: RoleUpsertRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("admin.roles.manage")),
) -> dict:
    item = create_role(db, code=payload.code, name=payload.name, description=payload.description, actor_user_id=current_user.id)
    return success_response(item.model_dump(mode="json"))


@router.patch("/roles/{role_id}")
def patch_role(
    role_id: UUID,
    payload: RoleUpsertRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("admin.roles.manage")),
) -> dict:
    item = update_role(
        db,
        role_id=role_id,
        code=payload.code,
        name=payload.name,
        description=payload.description,
        actor_user_id=current_user.id,
    )
    return success_response(item.model_dump(mode="json"))


@router.post("/roles/{role_id}/permissions")
def post_role_permissions(
    role_id: UUID,
    payload: RolePermissionsRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("admin.roles.manage")),
) -> dict:
    item = set_role_permissions(db, role_id=role_id, permission_codes=payload.permission_codes, actor_user_id=current_user.id)
    return success_response(item.model_dump(mode="json"))


@router.post("/roles/{role_id}/disable")
def disable_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("admin.roles.manage")),
) -> dict:
    item = set_role_status(db, role_id=role_id, enabled=False, actor_user_id=current_user.id)
    return success_response(item.model_dump(mode="json"))


@router.post("/roles/{role_id}/enable")
def enable_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("admin.roles.manage")),
) -> dict:
    item = set_role_status(db, role_id=role_id, enabled=True, actor_user_id=current_user.id)
    return success_response(item.model_dump(mode="json"))
