"""FastAPI 依赖：Bearer 解析、当前用户、权限/角色装饰器工厂。"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, is_jwt_error
from app.core.database import get_db
from app.models.user import User
from app.services.auth import get_user_permissions, get_user_roles

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    """已从 access token 解析并加载权限后的当前用户视图（非 ORM 实体）。"""

    id: UUID
    username: str
    display_name: str
    email: str | None
    status: str
    roles: list[str]
    permissions: list[str]


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """要求请求携带合法 Bearer access token，否则 401。"""
    return _resolve_current_user(credentials, db)


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser | None:
    """无 Authorization 时返回 None；token 无效仍抛 401。"""
    if credentials is None:
        return None
    try:
        return _resolve_current_user(credentials, db)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        raise


def _resolve_current_user(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
) -> CurrentUser:
    """校验 JWT typ=sub，加载活跃用户及角色权限列表。"""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        token_type = payload.get("typ")
    except Exception as exc:
        if is_jwt_error(exc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 无效") from exc
        raise

    if token_type != "access" or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 无效")

    try:
        user_uuid = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 无效") from exc

    user = db.execute(select(User).where(User.id == user_uuid)).scalar_one_or_none()
    if user is None or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或不可用")

    roles = get_user_roles(db, user.id)
    permissions = get_user_permissions(db, user.id)
    return CurrentUser(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        status=user.status,
        roles=roles,
        permissions=permissions,
    )


def require_permissions(*required_permissions: str):
    """依赖工厂：当前用户须同时具备给定权限点集合，否则 403。"""

    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not set(required_permissions).issubset(set(current_user.permissions)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return current_user

    return dependency


def require_any_permissions(*allowed_permissions: str):
    """依赖工厂：当前用户须具备任一列出的权限点，否则 403。"""

    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not set(allowed_permissions).intersection(set(current_user.permissions)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return current_user

    return dependency


def require_roles(*allowed_roles: str):
    """依赖工厂：当前用户须拥有任一列出的角色 code，否则 403。"""

    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not any(role in current_user.roles for role in allowed_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return current_user

    return dependency
