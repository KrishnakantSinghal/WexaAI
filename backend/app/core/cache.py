"""Lightweight Redis JSON cache helpers.

All helpers are best-effort: any Redis error degrades gracefully to a cache miss
so the calling endpoint still serves data from the database.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Awaitable, Callable, Optional

from app.core.logging import get_logger
from app.db.redis import get_redis_pool

logger = get_logger(__name__)


def make_key(*parts: Any) -> str:
    """Build a stable cache key from arbitrary parts."""
    return ":".join(str(p) for p in parts)


def hash_payload(payload: Any) -> str:
    """Stable short hash for cache-key suffixes (e.g. request bodies)."""
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.md5(raw).hexdigest()  # noqa: S324 — non-cryptographic use


async def cache_get_json(key: str) -> Optional[Any]:
    try:
        redis = await get_redis_pool()
        raw = await redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:  # noqa: BLE001 — cache must never break the app
        logger.warning("cache_get_failed", key=key, error=str(exc))
        return None


async def cache_set_json(key: str, value: Any, ttl: int) -> None:
    try:
        redis = await get_redis_pool()
        await redis.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache_set_failed", key=key, error=str(exc))


async def cache_delete(*keys: str) -> None:
    if not keys:
        return
    try:
        redis = await get_redis_pool()
        await redis.delete(*keys)
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache_delete_failed", keys=keys, error=str(exc))


async def cache_delete_prefix(prefix: str) -> None:
    """Delete all keys matching `<prefix>*` using SCAN (non-blocking)."""
    try:
        redis = await get_redis_pool()
        cursor = 0
        while True:
            cursor, keys = await redis.scan(
                cursor=cursor, match=f"{prefix}*", count=200
            )
            if keys:
                await redis.delete(*keys)
            if cursor == 0:
                break
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache_delete_prefix_failed", prefix=prefix, error=str(exc))


async def cached_json(key: str, ttl: int, loader: Callable[[], Awaitable[Any]]) -> Any:
    """Get-or-set helper. `loader` is invoked only on cache miss."""
    hit = await cache_get_json(key)
    if hit is not None:
        return hit
    value = await loader()
    await cache_set_json(key, value, ttl)
    return value
