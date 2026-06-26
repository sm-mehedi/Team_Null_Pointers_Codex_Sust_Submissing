from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import Channel, Language, TransactionStatus, TransactionType, UserType


class TransactionHistoryEntry(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    transaction_id: str = Field(min_length=1, max_length=128)
    timestamp: str = Field(min_length=1, max_length=64)
    type: TransactionType
    amount: float = Field(ge=0)
    counterparty: str = Field(min_length=1, max_length=128)
    status: TransactionStatus


class TicketRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    ticket_id: str = Field(min_length=1, max_length=128)
    complaint: str = Field(max_length=12000)
    language: Language | None = None
    channel: Channel | None = None
    user_type: UserType | None = None
    campaign_context: str | None = Field(default=None, max_length=256)
    transaction_history: list[TransactionHistoryEntry] = Field(default_factory=list, max_length=20)
    metadata: dict[str, Any] | None = None

    @field_validator("ticket_id")
    @classmethod
    def ticket_id_must_be_safe(cls, value: str) -> str:
        if any(ch in value for ch in "\r\n\t"):
            raise ValueError("ticket_id contains invalid whitespace")
        return value
