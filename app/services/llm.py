from __future__ import annotations

from app.config import Settings


class LLMAdvisor:
    def __init__(self, settings: Settings):
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.enabled = bool(settings.llm_api_key) and self.provider not in {"", "none"}

    def describe(self) -> dict[str, str | bool]:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "model": self.model,
            "mode": "rule_based_primary_optional_llm",
        }
