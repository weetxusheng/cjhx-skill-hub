from __future__ import annotations

from functools import lru_cache
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


def is_redis_available() -> bool:
    try:
        return bool(get_redis_client().ping())
    except RedisError:
        return False


def safe_redis_call(callback, *args: Any, **kwargs: Any) -> Any:
    try:
        client = get_redis_client()
        return callback(client, *args, **kwargs)
    except RedisError:
        return None
