from collections import Counter

from app.models.enums import CaseType, TransactionStatus, TransactionType
from app.models.request import TicketRequest
from app.utils.normalization import normalize_text


def classify_case(ticket: TicketRequest, safety_sensitive: bool) -> CaseType:
    text = normalize_text(ticket.complaint)

    if safety_sensitive:
        return CaseType.PHISHING_OR_SOCIAL_ENGINEERING
    if any(term in text for term in ("wrong number", "wrong recipient", "wrong person", "wrong account")):
        return CaseType.WRONG_TRANSFER
    if any(term in text for term in ("failed", "deducted", "not successful", "payment did not go")):
        return CaseType.PAYMENT_FAILED
    if "duplicate" in text or "twice" in text or "double charged" in text or _has_duplicate_payment(ticket):
        return CaseType.DUPLICATE_PAYMENT
    if "settlement" in text or ("merchant" in text and any(term in text for term in ("not received", "delayed", "pending"))):
        return CaseType.MERCHANT_SETTLEMENT_DELAY
    if ("cash in" in text or "cash-in" in text or "deposit" in text) and any(term in text for term in ("agent", "not reflected", "balance")):
        return CaseType.AGENT_CASH_IN_ISSUE
    if "refund" in text or "cashback" in text or "reverse" in text or "reversal" in text:
        return CaseType.REFUND_REQUEST

    for txn in ticket.transaction_history:
        if txn.type == TransactionType.SETTLEMENT:
            return CaseType.MERCHANT_SETTLEMENT_DELAY
        if txn.type == TransactionType.CASH_IN and txn.status != TransactionStatus.COMPLETED:
            return CaseType.AGENT_CASH_IN_ISSUE
        if txn.status == TransactionStatus.FAILED:
            return CaseType.PAYMENT_FAILED

    return CaseType.OTHER


def _has_duplicate_payment(ticket: TicketRequest) -> bool:
    keys = Counter(
        (txn.type, txn.amount, txn.counterparty)
        for txn in ticket.transaction_history
        if txn.type in {TransactionType.PAYMENT, TransactionType.TRANSFER}
    )
    return any(count > 1 for count in keys.values())
