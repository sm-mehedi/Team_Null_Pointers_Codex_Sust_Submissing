from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from app.config import Settings
from app.services.redis_client import RedisStore


class RateLimiter:
    def __init__(self, settings: Settings, redis: RedisStore):
        self._settings = settings
        self._redis = redis
        self._memory: dict[str, deque[float]] = defaultdict(deque)

    async def check(self, request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        window = self._settings.rate_limit_window_seconds
        limit = self._settings.rate_limit_requests
        bucket = int(time.time() // window)
        key = f"rate-limit:{client}:{bucket}"

        count = await self._redis.increment_window(key, window)
        if count is None:
            now = time.time()
            hits = self._memory[client]
            while hits and hits[0] <= now - window:
                hits.popleft()
            hits.append(now)
            count = len(hits)

        if count > limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limited",
                    "message": "Too many requests. Please retry after the rate limit window.",
                },
            )
