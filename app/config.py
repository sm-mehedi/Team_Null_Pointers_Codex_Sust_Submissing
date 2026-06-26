from __future__ import annotations

from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="production", validation_alias="ENVIRONMENT")
    port: int = Field(default=8000, validation_alias="PORT")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    allowed_origins: str = Field(default="*", validation_alias="ALLOWED_CORS_ORIGINS")
    max_complaint_chars: int = Field(default=4000, validation_alias="MAX_COMPLAINT_CHARS")
    high_value_amount: float = Field(default=10000, validation_alias="HIGH_VALUE_AMOUNT")
    critical_value_amount: float = Field(default=50000, validation_alias="CRITICAL_VALUE_AMOUNT")
    llm_provider: str = Field(default="none", validation_alias="LLM_PROVIDER")
    llm_model: str = Field(default="none", validation_alias="LLM_MODEL")
    llm_api_key: SecretStr | None = Field(default=None, validation_alias="LLM_API_KEY")
    redis_url: SecretStr | None = Field(default=None, validation_alias="REDIS_URL")
    upstash_redis_url: SecretStr | None = Field(default=None, validation_alias="UPSTASH_REDIS_URL")
    cache_ttl_seconds: int = Field(default=300, validation_alias="CACHE_TTL_SECONDS")
    session_ttl_seconds: int = Field(default=3600, validation_alias="SESSION_TTL_SECONDS")
    rate_limit_requests: int = Field(default=60, validation_alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, validation_alias="RATE_LIMIT_WINDOW_SECONDS")
    enable_frontend: bool = Field(default=True, validation_alias="ENABLE_FRONTEND")

    @property
    def effective_redis_url(self) -> str | None:
        secret = self.redis_url or self.upstash_redis_url
        return secret.get_secret_value() if secret else None

    @property
    def allowed_cors_origins(self) -> list[str]:
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
