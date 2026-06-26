from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CaseType, Department, EvidenceVerdict, Severity


class HealthResponse(BaseModel):
    status: str = "ok"


class TicketAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticket_id: str
    relevant_transaction_id: str | None
    evidence_verdict: EvidenceVerdict
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str = Field(min_length=1, max_length=800)
    recommended_next_action: str = Field(min_length=1, max_length=800)
    customer_reply: str = Field(min_length=1, max_length=1000)
    human_review_required: bool
    confidence: float | None = Field(default=None, ge=0, le=1)
    reason_codes: list[str] | None = Field(default=None, max_length=12)
