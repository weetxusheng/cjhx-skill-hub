"""治理域只读查询模型：系统角色联系人等面向前台/轻量消费的结构。"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.schemas.admin import DepartmentBrief


class SystemRoleContactRoleItem(BaseModel):
    """命中的系统角色摘要。"""

    code: str
    name: str


class SystemRoleContactItem(BaseModel):
    """可联系用户摘要，仅保留前台展示必要字段。"""

    id: UUID
    display_name: str
    primary_department: DepartmentBrief | None = None
    matched_roles: list[SystemRoleContactRoleItem]


class SystemRoleContactsResponse(BaseModel):
    """按系统角色查询联系人时的返回载荷。"""

    requested_roles: list[SystemRoleContactRoleItem]
    items: list[SystemRoleContactItem]
    total: int
