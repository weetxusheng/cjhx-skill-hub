from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_any_permissions, require_permissions
from app.schemas.category import CategoryUpsertRequest
from app.schemas.common import success_response
from app.services.governance import (
    create_category,
    delete_category,
    list_admin_categories as list_admin_categories_service,
    update_category,
)

router = APIRouter()


@router.get("/categories")
def list_admin_categories(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permissions("admin.categories.view")),
) -> dict:
    items = [item.model_dump(mode="json") for item in list_admin_categories_service(db)]
    return success_response(items)


@router.get("/categories/options")
def list_category_options(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_any_permissions("admin.categories.view", "skill.view")),
) -> dict:
    items = [item.model_dump(mode="json") for item in list_admin_categories_service(db)]
    return success_response(items)


@router.post("/categories")
def post_category(
    payload: CategoryUpsertRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("admin.categories.manage")),
) -> dict:
    item = create_category(db, payload=payload, actor_user_id=current_user.id)
    return success_response(item.model_dump(mode="json"))


@router.patch("/categories/{category_id}")
def patch_category(
    category_id: UUID,
    payload: CategoryUpsertRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("admin.categories.manage")),
) -> dict:
    item = update_category(db, category_id=category_id, payload=payload, actor_user_id=current_user.id)
    return success_response(item.model_dump(mode="json"))


@router.delete("/categories/{category_id}")
def remove_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permissions("admin.categories.manage")),
) -> dict:
    delete_category(db, category_id=category_id, actor_user_id=current_user.id)
    return success_response({"deleted": True})
