from __future__ import annotations

import logging
from typing import Any

from app.config import Settings

logger = logging.getLogger(__name__)


class RedisStore:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: Any | None = None
        self._available = False

    @property
    def available(self) -> bool:
        return self._available

    async def connect(self) -> None:
        redis_url = self._settings.effective_redis_url
        if not redis_url:
            logger.info("Redis/Upstash not configured; using in-memory fallbacks")
            return

        try:
            from redis.asyncio import Redis

            self._client = Redis.from_url(redis_url, decode_responses=True)
            await self._client.ping()
            self._available = True
            logger.info("Redis/Upstash connection verified")
        except Exception:
            self._client = None
            self._available = False
            logger.exception("Redis/Upstash connection failed; using in-memory fallbacks")

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def health(self) -> dict[str, str]:
        if not self._client:
            return {"status": "not_configured", "provider": "memory"}
        try:
            await self._client.ping()
            return {"status": "ok", "provider": "redis"}
        except Exception:
            logger.exception("Redis health check failed")
            return {"status": "error", "provider": "redis"}

    async def get(self, key: str) -> str | None:
        if not self._client:
            return None
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        if self._client:
            await self._client.set(key, value, ex=ttl_seconds)

    async def increment_window(self, key: str, ttl_seconds: int) -> int | None:
        if not self._client:
            return None
        count = await self._client.incr(key)
        if count == 1:
            await self._client.expire(key, ttl_seconds)
        return int(count)
