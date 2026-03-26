from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserSummary(BaseModel):
    id: UUID
    username: str
    display_name: str
    email: str | None
    status: Literal["active", "disabled"]
    roles: list[str]
    permissions: list[str]
    last_login_at: datetime | None


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserSummary
