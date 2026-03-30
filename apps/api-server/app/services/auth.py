from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.core.redis import safe_redis_call
from app.models.refresh_token import RefreshToken
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.auth import UserSummary

settings = get_settings()


def _refresh_token_cache_key(token_hash: str) -> str:
    """生成 refresh token 撤销标记在缓存中的 key。

    参数:
    - token_hash: refresh token 的哈希值。

    返回:
    - Redis 中用于标记该 token 已失效的键名。
    """
    return f"refresh-token:revoked:{token_hash}"


def _mark_token_revoked_in_cache(token_hash: str) -> None:
    """将 refresh token 标记为“已撤销”并写入缓存。

    说明:
    - TTL 与 refresh token 过期时间保持同级别，避免缓存无限增长。
    - 该标记用于快速拒绝已撤销 token，减少数据库命中。
    """
    ttl_seconds = settings.jwt_refresh_expire_days * 24 * 3600
    safe_redis_call(lambda redis_client: redis_client.setex(_refresh_token_cache_key(token_hash), ttl_seconds, "1"))


def get_user_roles(db: Session, user_id: UUID) -> list[str]:
    """查询用户当前生效的角色编码列表。

    规则:
    - 仅返回激活角色（`Role.is_active = True`）。
    """
    rows = db.execute(
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id, Role.is_active.is_(True))
    ).scalars()
    return list(rows)


def get_user_permissions(db: Session, user_id: UUID) -> list[str]:
    """查询用户当前生效的权限编码列表。

    规则:
    - 权限来自“用户角色 -> 角色权限”映射。
    - 去重后按字典序返回，便于前端稳定渲染与比较。
    """
    rows = db.execute(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id, Role.is_active.is_(True))
        .distinct()
    ).scalars()
    return sorted(rows)


def build_user_summary(db: Session, user: User) -> UserSummary:
    """构建登录态用户摘要对象。

    内容:
    - 基础信息（id、用户名、展示名、邮箱、状态）
    - 当前角色与权限
    - 最近登录时间
    """
    return UserSummary(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        status=user.status,
        roles=get_user_roles(db, user.id),
        permissions=get_user_permissions(db, user.id),
        last_login_at=user.last_login_at,
    )


def authenticate_sso_portal_user(db: Session, loginname_hex: str, sign: str) -> User:
    """校验主系统下发的单点参数，解码后与本地用户匹配并返回用户实体。

    边界:
    - 解码失败、用户不存在或非 active 时统一返回 401「单点登录失败」，避免枚举用户名。

    副作用:
    - 无；调用方在成功后自行 `issue_tokens`。
    """
    from app.services.sso_gateway_decode import decode_sso_login_name

    username = decode_sso_login_name(loginname_hex.strip(), sign.strip())
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="单点登录失败")
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if user is None or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="单点登录失败")
    return user


def authenticate_user(db: Session, username: str, password: str) -> User:
    """校验用户名密码并返回用户对象。

    异常:
    - 401: 用户不存在或密码错误。
    - 403: 用户已被禁用。
    """
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")
    return user


def issue_tokens(db: Session, user: User) -> tuple[str, str]:
    """为用户签发 access token 与 refresh token。

    副作用:
    - 新增一条 refresh token 记录（仅存哈希）。
    - 更新用户最近登录时间。
    - 提交事务。
    """
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token()
    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=refresh_token_expiry(),
    )
    db.add(token_record)
    user.last_login_at = datetime.now(UTC)
    db.commit()
    db.refresh(user)
    return access_token, refresh_token


def refresh_tokens(db: Session, raw_refresh_token: str) -> tuple[User, str, str]:
    """使用 refresh token 换发新的 access/refresh token。

    流程:
    1) 先查缓存撤销标记，命中即直接拒绝。
    2) 再查数据库 token 记录，校验未撤销且未过期。
    3) 校验用户状态必须为 active。
    4) 撤销旧 token、写缓存标记、签发新 token 并落库。

    返回:
    - (user, new_access_token, new_refresh_token)
    """
    token_hash = hash_refresh_token(raw_refresh_token)
    if safe_redis_call(lambda redis_client: redis_client.exists(_refresh_token_cache_key(token_hash))):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token 无效")
    token_record = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).scalar_one_or_none()
    if token_record is None or token_record.revoked_at is not None or token_record.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token 无效")

    user = db.execute(select(User).where(User.id == token_record.user_id)).scalar_one()
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")

    token_record.revoked_at = datetime.now(UTC)
    _mark_token_revoked_in_cache(token_hash)
    new_access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(new_refresh_token),
            expires_at=refresh_token_expiry(),
        )
    )
    db.commit()
    return user, new_access_token, new_refresh_token


def revoke_refresh_token(db: Session, raw_refresh_token: str) -> None:
    """撤销单个 refresh token。

    副作用:
    - 将数据库中对应 token 标记 revoked_at。
    - 写入缓存撤销标记，加速后续拦截。
    """
    token_hash = hash_refresh_token(raw_refresh_token)
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    db.commit()
    _mark_token_revoked_in_cache(token_hash)


def revoke_all_user_refresh_tokens(db: Session, user_id: UUID) -> None:
    """撤销某个用户当前所有未撤销 refresh token。

    场景:
    - 用户被禁用、权限调整或主动全端登出时。

    副作用:
    - 批量更新数据库 token 状态。
    - 为每个原活跃 token 写缓存撤销标记。
    """
    active_hashes = list(
        db.execute(
            select(RefreshToken.token_hash).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        ).scalars()
    )
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    db.commit()
    for token_hash in active_hashes:
        _mark_token_revoked_in_cache(token_hash)
