"""认证相关请求/响应模型（登录、刷新、登出、用户摘要）。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """用户名密码登录体。"""

    username: str
    password: str


class SsoPortalRequest(BaseModel):
    """主系统网关跳转携带的 `loginname`（hex）与 `sign`，与查询参数同名。"""

    loginname: str
    sign: str


class RefreshRequest(BaseModel):
    """使用 refresh_token 换新令牌。"""

    refresh_token: str


class LogoutRequest(BaseModel):
    """注销时提交的 refresh_token（服务端作废对应记录）。"""

    refresh_token: str


class UserSummary(BaseModel):
    """返回给前端的当前用户摘要（含角色与权限点）。"""

    id: UUID
    username: str
    display_name: str
    email: str | None
    status: Literal["active", "disabled"]
    roles: list[str]
    permissions: list[str]
    last_login_at: datetime | None


class AuthTokens(BaseModel):
    """双令牌结构（可与 AuthResponse 组合使用）。"""

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class AuthResponse(BaseModel):
    """登录/刷新成功时的完整载荷。"""

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserSummary
