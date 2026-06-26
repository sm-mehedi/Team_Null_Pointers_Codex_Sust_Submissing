from __future__ import annotations

import hashlib
import json
import time

from app.config import Settings
from app.models.request import TicketRequest
from app.models.response import TicketAnalysisResponse
from app.services.redis_client import RedisStore


class ResponseCache:
    def __init__(self, settings: Settings, redis: RedisStore):
        self._settings = settings
        self._redis = redis
        self._memory: dict[str, tuple[float, str]] = {}

    def key_for(self, ticket: TicketRequest) -> str:
        payload = ticket.model_dump(mode="json")
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        return f"ticket-cache:{digest}"

    async def get(self, key: str) -> TicketAnalysisResponse | None:
        raw = await self._redis.get(key)
        if raw is None:
            item = self._memory.get(key)
            if item:
                expires_at, raw = item
                if expires_at < time.time():
                    self._memory.pop(key, None)
                    return None
        if not raw:
            return None
        return TicketAnalysisResponse.model_validate_json(raw)

    async def set(self, key: str, response: TicketAnalysisResponse) -> None:
        raw = response.model_dump_json()
        ttl = self._settings.cache_ttl_seconds
        await self._redis.set(key, raw, ttl)
        self._memory[key] = (time.time() + ttl, raw)


class SessionMemory:
    def __init__(self, settings: Settings, redis: RedisStore):
        self._settings = settings
        self._redis = redis
        self._memory: dict[str, tuple[float, str]] = {}

    async def remember(self, response: TicketAnalysisResponse) -> None:
        key = f"ticket-session:{response.ticket_id}"
        raw = response.model_dump_json()
        ttl = self._settings.session_ttl_seconds
        await self._redis.set(key, raw, ttl)
        self._memory[key] = (time.time() + ttl, raw)

    async def get(self, ticket_id: str) -> TicketAnalysisResponse | None:
        key = f"ticket-session:{ticket_id}"
        raw = await self._redis.get(key)
        if raw is None:
            item = self._memory.get(key)
            if item:
                expires_at, raw = item
                if expires_at < time.time():
                    self._memory.pop(key, None)
                    return None
        return TicketAnalysisResponse.model_validate_json(raw) if raw else None
