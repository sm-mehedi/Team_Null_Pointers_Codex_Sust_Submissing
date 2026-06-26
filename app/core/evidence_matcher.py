from dataclasses import dataclass
from decimal import Decimal
import re

from app.models.enums import EvidenceVerdict, TransactionStatus, TransactionType
from app.models.request import TicketRequest, TransactionHistoryEntry
from app.utils.normalization import digits_only, normalize_text


@dataclass(frozen=True)
class EvidenceResult:
    transaction: TransactionHistoryEntry | None
    verdict: EvidenceVerdict
    reason_codes: list[str]
    confidence: float


AMOUNT_PATTERN = re.compile(r"(?<!\d)(\d{2,8})(?:\s*(?:bdt|tk|taka))?", re.IGNORECASE)


def extract_amounts(complaint: str) -> list[Decimal]:
    amounts: list[Decimal] = []
    for match in AMOUNT_PATTERN.finditer(complaint):
        try:
            amount = Decimal(match.group(1))
        except Exception:
            continue
        if amount > 0:
            amounts.append(amount)
    return amounts


def _type_hints(text: str) -> set[TransactionType]:
    hints: set[TransactionType] = set()
    if any(term in text for term in ("sent", "transfer", "wrong number", "wrong recipient", "wrong person")):
        hints.add(TransactionType.TRANSFER)
    if any(term in text for term in ("payment", "merchant", "paid", "cashback", "charged")):
        hints.add(TransactionType.PAYMENT)
    if "cash in" in text or "cash-in" in text or "deposit" in text:
        hints.add(TransactionType.CASH_IN)
    if "cash out" in text or "cash-out" in text or "withdraw" in text:
        hints.add(TransactionType.CASH_OUT)
    if "settlement" in text:
        hints.add(TransactionType.SETTLEMENT)
    if "refund" in text or "reversal" in text:
        hints.add(TransactionType.REFUND)
    return hints


def _status_supported(text: str, transaction: TransactionHistoryEntry) -> bool:
    if any(term in text for term in ("failed", "deducted", "not successful")):
        return transaction.status in {TransactionStatus.FAILED, TransactionStatus.PENDING}
    if any(term in text for term in ("completed", "sent", "paid", "charged")):
        return transaction.status == TransactionStatus.COMPLETED
    if "reversed" in text or "returned" in text:
        return transaction.status == TransactionStatus.REVERSED
    return True


def match_evidence(ticket: TicketRequest) -> EvidenceResult:
    transactions = ticket.transaction_history
    if not transactions:
        return EvidenceResult(None, EvidenceVerdict.INSUFFICIENT_DATA, ["no_transaction_history"], 0.35)

    text = normalize_text(ticket.complaint)
    amounts = extract_amounts(ticket.complaint)
    type_hints = _type_hints(text)
    complaint_digits = digits_only(text)

    scored: list[tuple[int, TransactionHistoryEntry, list[str]]] = []
    for txn in transactions:
        score = 0
        reasons: list[str] = []

        if amounts and txn.amount in amounts:
            score += 5
            reasons.append("amount_match")
        if not amounts:
            score += 1

        if type_hints and txn.type in type_hints:
            score += 3
            reasons.append("transaction_type_match")

        counterparty_digits = digits_only(txn.counterparty)
        if counterparty_digits and counterparty_digits[-6:] and counterparty_digits[-6:] in complaint_digits:
            score += 4
            reasons.append("counterparty_match")

        if _status_supported(text, txn):
            score += 2
            reasons.append("status_supports_claim")
        elif any(term in text for term in ("failed", "deducted", "completed", "sent", "paid", "reversed")):
            score -= 3
            reasons.append("status_contradiction")

        scored.append((score, txn, reasons))

    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best_txn, reasons = scored[0]

    if best_score <= 1:
        return EvidenceResult(None, EvidenceVerdict.INSUFFICIENT_DATA, ["no_matching_transaction"], 0.4)

    if "status_contradiction" in reasons:
        return EvidenceResult(best_txn, EvidenceVerdict.INCONSISTENT, reasons, 0.72)

    if amounts and best_txn.amount not in amounts:
        return EvidenceResult(best_txn, EvidenceVerdict.INCONSISTENT, reasons + ["amount_mismatch"], 0.65)

    confidence = min(0.95, 0.55 + best_score / 12)
    return EvidenceResult(best_txn, EvidenceVerdict.CONSISTENT, reasons, confidence)
