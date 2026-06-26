from app.core.classifier import classify_case
from app.core.evidence_matcher import match_evidence
from app.core.router import route_department
from app.core.safety import inspect_complaint, sanitize_customer_reply
from app.core.severity import determine_severity, requires_human_review
from app.core.text_templates import build_agent_summary, build_customer_reply, build_next_action
from app.models.request import TicketRequest
from app.models.response import TicketAnalysisResponse


class DecisionEngine:
    def analyze(self, ticket: TicketRequest) -> TicketAnalysisResponse:
        return analyze_ticket(ticket)


def analyze_ticket(ticket: TicketRequest) -> TicketAnalysisResponse:
    safety = inspect_complaint(ticket.complaint)
    evidence = match_evidence(ticket)
    case_type = classify_case(ticket, safety.is_suspicious)
    department = route_department(case_type)
    severity = determine_severity(case_type, evidence.verdict, evidence.transaction, safety.has_prompt_injection)
    human_review_required = requires_human_review(
        case_type=case_type,
        severity=severity,
        verdict=evidence.verdict,
        prompt_injection=safety.has_prompt_injection,
    )

    reason_codes = []
    reason_codes.extend(safety.reason_codes)
    reason_codes.extend(evidence.reason_codes)
    reason_codes.append(str(case_type))
    if human_review_required:
        reason_codes.append("human_review_required")

    customer_reply = sanitize_customer_reply(build_customer_reply(case_type, evidence.verdict, evidence.transaction))

    return TicketAnalysisResponse(
        ticket_id=ticket.ticket_id,
        relevant_transaction_id=evidence.transaction.transaction_id if evidence.transaction else None,
        evidence_verdict=evidence.verdict,
        case_type=case_type,
        severity=severity,
        department=department,
        agent_summary=build_agent_summary(ticket, evidence.transaction, evidence.verdict, case_type),
        recommended_next_action=build_next_action(case_type, evidence.verdict, evidence.transaction),
        customer_reply=customer_reply,
        human_review_required=human_review_required,
        confidence=round(evidence.confidence, 2),
        reason_codes=list(dict.fromkeys(reason_codes)),
    )
