from __future__ import annotations

from fastapi import Request

from app.core.decision_engine import DecisionEngine
from app.services.cache import ResponseCache, SessionMemory
from app.services.llm import LLMAdvisor
from app.services.rate_limiter import RateLimiter
from app.services.redis_client import RedisStore


def get_engine() -> DecisionEngine:
    return DecisionEngine()


def get_redis_store(request: Request) -> RedisStore:
    return request.app.state.redis


def get_response_cache(request: Request) -> ResponseCache:
    return request.app.state.response_cache


def get_session_memory(request: Request) -> SessionMemory:
    return request.app.state.session_memory


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


def get_llm_advisor(request: Request) -> LLMAdvisor:
    return request.app.state.llm_advisor
