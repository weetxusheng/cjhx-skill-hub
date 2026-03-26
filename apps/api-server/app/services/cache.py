from __future__ import annotations

import json
from typing import Any

from app.core.redis import safe_redis_call


def get_cached_json(key: str) -> Any | None:
    value = safe_redis_call(lambda redis_client: redis_client.get(key))
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def set_cached_json(key: str, payload: Any, ttl_seconds: int) -> None:
    safe_redis_call(
        lambda redis_client: redis_client.setex(key, ttl_seconds, json.dumps(payload, ensure_ascii=False, default=str))
    )


def delete_cached_json(*keys: str) -> None:
    if not keys:
        return
    safe_redis_call(lambda redis_client: redis_client.delete(*keys))
