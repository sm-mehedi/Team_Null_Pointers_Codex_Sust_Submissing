from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import get_settings
from app.core.decision_engine import DecisionEngine
from app.dependencies import (
    get_engine,
    get_llm_advisor,
    get_rate_limiter,
    get_redis_store,
    get_response_cache,
    get_session_memory,
)
from app.models.request import TicketRequest
from app.models.response import HealthResponse, TicketAnalysisResponse
from app.services.cache import ResponseCache, SessionMemory
from app.services.llm import LLMAdvisor
from app.services.rate_limiter import RateLimiter
from app.services.redis_client import RedisStore

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/health/redis")
async def redis_health(redis: RedisStore = Depends(get_redis_store)) -> dict[str, str]:
    return await redis.health()


@router.get("/health/llm")
async def llm_health(llm: LLMAdvisor = Depends(get_llm_advisor)) -> dict[str, str | bool]:
    return llm.describe()


@router.post("/analyze-ticket", response_model=TicketAnalysisResponse)
async def analyze_ticket(
    request_body: TicketRequest,
    request: Request,
    engine: DecisionEngine = Depends(get_engine),
    cache: ResponseCache = Depends(get_response_cache),
    session_memory: SessionMemory = Depends(get_session_memory),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> TicketAnalysisResponse:
    settings = get_settings()
    await rate_limiter.check(request)
    if not request_body.complaint or not request_body.complaint.strip():
        raise HTTPException(
            status_code=422,
            detail={
                "error": "empty_complaint",
                "message": "Complaint must contain meaningful text.",
            },
        )
    if len(request_body.complaint) > settings.max_complaint_chars:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "complaint_too_large",
                "message": "Complaint exceeds the configured maximum length.",
            },
        )
    cache_key = cache.key_for(request_body)
    cached = await cache.get(cache_key)
    if cached:
        return cached

    response = engine.analyze(request_body)
    await cache.set(cache_key, response)
    await session_memory.remember(response)
    return response
