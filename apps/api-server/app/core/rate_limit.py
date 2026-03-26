from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.core.redis import safe_redis_call


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    count: int
    window_seconds: int


def parse_rate_limit(raw_value: str) -> RateLimitRule:
    try:
        count_raw, unit = raw_value.strip().split("/", 1)
        count = int(count_raw)
    except ValueError as exc:
        raise ValueError(f"Invalid rate limit: {raw_value}")
    if unit not in {"second", "minute", "hour"}:
        raise ValueError(f"Invalid rate limit unit: {raw_value}")
    window_seconds = {"second": 1, "minute": 60, "hour": 3600}[unit]
    return RateLimitRule(count=count, window_seconds=window_seconds)


def enforce_rate_limit(*, scope: str, actor_key: str, rule_raw: str) -> None:
    rule = parse_rate_limit(rule_raw)
    bucket = int(datetime.now(UTC).timestamp()) // rule.window_seconds
    redis_key = f"rate-limit:{scope}:{actor_key}:{bucket}"

    def _increment(redis_client):
        current = redis_client.incr(redis_key)
        if current == 1:
            redis_client.expire(redis_key, rule.window_seconds)
        return current

    current = safe_redis_call(_increment)
    if current is None:
        return
    if int(current) > rule.count:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="请求过于频繁，请稍后再试")
