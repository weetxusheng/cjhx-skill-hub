"""Redis 客户端单例与容错调用（不可用时限流等降级为 no-op）。"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings


@lru_cache
def get_redis_client() -> Redis:
    """返回全局 Redis 连接（decode_responses=True）。"""
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


def is_redis_available() -> bool:
    """探测 Redis 是否可 ping 通。"""
    try:
        return bool(get_redis_client().ping())
    except RedisError:
        return False


def safe_redis_call(callback, *args: Any, **kwargs: Any) -> Any:
    """执行 Redis 回调；连接失败时返回 None，不抛错（调用方自行降级）。"""
    try:
        client = get_redis_client()
        return callback(client, *args, **kwargs)
    except RedisError:
        return None
