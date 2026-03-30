"""基于 Redis 的滑动窗口限流（配置形如 `20/hour`）。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.core.redis import safe_redis_call


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    """解析后的限流规则：窗口内允许次数与窗口长度（秒）。"""

    count: int
    window_seconds: int


def parse_rate_limit(raw_value: str) -> RateLimitRule:
    """解析 `次数/单位` 字符串，单位支持 second、minute、hour。"""
    try:
        count_raw, unit = raw_value.strip().split("/", 1)
        count = int(count_raw)
    except ValueError:
        raise ValueError(f"Invalid rate limit: {raw_value}")
    if unit not in {"second", "minute", "hour"}:
        raise ValueError(f"Invalid rate limit unit: {raw_value}")
    window_seconds = {"second": 1, "minute": 60, "hour": 3600}[unit]
    return RateLimitRule(count=count, window_seconds=window_seconds)


def enforce_rate_limit(*, scope: str, actor_key: str, rule_raw: str) -> None:
    """对 `scope:actor_key` 递增计数；超限抛 429。Redis 不可用时跳过限流。"""
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
