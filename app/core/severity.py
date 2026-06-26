from decimal import Decimal

from app.models.enums import CaseType, EvidenceVerdict, Severity
from app.models.request import TransactionHistoryEntry


HIGH_VALUE_AMOUNT = Decimal("5000")
CRITICAL_VALUE_AMOUNT = Decimal("25000")


def determine_severity(
    case_type: CaseType,
    verdict: EvidenceVerdict,
    transaction: TransactionHistoryEntry | None,
    prompt_injection: bool,
) -> Severity:
    amount = transaction.amount if transaction else Decimal("0")

    if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING or prompt_injection:
        return Severity.CRITICAL
    if amount >= CRITICAL_VALUE_AMOUNT:
        return Severity.CRITICAL
    if case_type == CaseType.WRONG_TRANSFER:
        return Severity.HIGH
    if amount >= HIGH_VALUE_AMOUNT:
        return Severity.HIGH
    if verdict == EvidenceVerdict.INSUFFICIENT_DATA:
        return Severity.MEDIUM
    if case_type in {
        CaseType.PAYMENT_FAILED,
        CaseType.DUPLICATE_PAYMENT,
        CaseType.MERCHANT_SETTLEMENT_DELAY,
        CaseType.AGENT_CASH_IN_ISSUE,
    }:
        return Severity.MEDIUM
    return Severity.LOW


def requires_human_review(
    case_type: CaseType,
    severity: Severity,
    verdict: EvidenceVerdict,
    prompt_injection: bool,
) -> bool:
    return (
        prompt_injection
        or case_type
        in {
            CaseType.WRONG_TRANSFER,
            CaseType.PHISHING_OR_SOCIAL_ENGINEERING,
            CaseType.DUPLICATE_PAYMENT,
        }
        or severity in {Severity.HIGH, Severity.CRITICAL}
        or verdict != EvidenceVerdict.CONSISTENT
    )
