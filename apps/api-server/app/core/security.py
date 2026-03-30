"""密码哈希、JWT access/refresh 的创建与校验辅助函数。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import secrets
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import get_settings

password_hasher = PasswordHasher()
settings = get_settings()


def hash_password(password: str) -> str:
    """使用 Argon2 生成密码哈希（入库字段）。"""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """校验明文密码是否与存储哈希一致。"""
    try:
        return password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def create_access_token(subject: str) -> str:
    """签发 access JWT（typ=access，过期时间见配置分钟数）。"""
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "typ": "access", "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    """解码并校验 access JWT；过期或签名错误由 jose 抛错。"""
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def create_refresh_token() -> str:
    """生成随机 refresh 明文（入库仅存 SHA256）。"""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """refresh 明文转 SHA256 十六进制，用于表内查找与比对。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_token_expiry() -> datetime:
    """refresh 记录过期时间（UTC，天数见配置）。"""
    return datetime.now(UTC) + timedelta(days=settings.jwt_refresh_expire_days)


def is_jwt_error(exc: Exception) -> bool:
    """判断异常是否为 JWT 解码类错误，便于统一转 401。"""
    return isinstance(exc, JWTError)
