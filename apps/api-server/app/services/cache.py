from __future__ import annotations

import json
from typing import Any

from app.core.redis import safe_redis_call


def get_cached_json(key: str) -> Any | None:
    """读取并反序列化 JSON 缓存值。

    参数:
    - key: 缓存键。

    返回:
    - 反序列化后的对象；不存在或 JSON 非法时返回 None。
    """
    value = safe_redis_call(lambda redis_client: redis_client.get(key))
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def set_cached_json(key: str, payload: Any, ttl_seconds: int) -> None:
    """写入 JSON 缓存并设置过期时间。

    参数:
    - key: 缓存键。
    - payload: 可 JSON 序列化对象（对不可直接序列化字段会回退为字符串）。
    - ttl_seconds: 过期秒数。
    """
    safe_redis_call(
        lambda redis_client: redis_client.setex(key, ttl_seconds, json.dumps(payload, ensure_ascii=False, default=str))
    )


def delete_cached_json(*keys: str) -> None:
    """批量删除缓存键。

    说明:
    - 传入空参数时直接返回，不触发 Redis 调用。
    """
    if not keys:
        return
    safe_redis_call(lambda redis_client: redis_client.delete(*keys))
