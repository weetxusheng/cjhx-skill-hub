"""门户联系人查询：按系统角色返回可联系人员。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_db
from app.schemas.common import success_response
from app.services.governance import list_system_role_contacts

router = APIRouter()


@router.get("/system-role-contacts")
def get_system_role_contacts(
    role_codes: list[str] | None = Query(default=None, alias="role_code"),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    """按一个或多个系统角色查询当前可联系用户；需登录。"""
    payload = list_system_role_contacts(db, role_codes=role_codes or [])
    return success_response(payload.model_dump(mode="json"))
