from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import Settings, get_settings
from app.services.cache import ResponseCache, SessionMemory
from app.services.llm import LLMAdvisor
from app.services.rate_limiter import RateLimiter
from app.services.redis_client import RedisStore
from app.utils.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    redis = RedisStore(settings)
    await redis.connect()
    app.state.started_at = time.time()
    app.state.settings = settings
    app.state.redis = redis
    app.state.response_cache = ResponseCache(settings, redis)
    app.state.session_memory = SessionMemory(settings, redis)
    app.state.rate_limiter = RateLimiter(settings, redis)
    app.state.llm_advisor = LLMAdvisor(settings)
    logging.getLogger(__name__).info("QueueStorm Investigator started")
    try:
        yield
    finally:
        await redis.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="QueueStorm Investigator",
        description="Evidence-grounded fintech support ticket analysis API.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        logging.getLogger("app.request").info(
            "request complete",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
            },
        )
        response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": "invalid_request",
                "message": "Request JSON is malformed or missing required fields.",
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logging.getLogger(__name__).exception("Unhandled API error")
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "The service could not analyze this ticket safely.",
            },
        )

    app.include_router(router)
    static_dir = Path(__file__).resolve().parent / "static"
    if settings.enable_frontend and static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
    return app


app = create_app()
