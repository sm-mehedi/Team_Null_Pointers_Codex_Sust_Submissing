from app.models.enums import CaseType, EvidenceVerdict
from app.models.request import TicketRequest, TransactionHistoryEntry


def build_agent_summary(
    ticket: TicketRequest,
    transaction: TransactionHistoryEntry | None,
    verdict: EvidenceVerdict,
    case_type: CaseType,
) -> str:
    txn_text = (
        f"Relevant transaction {transaction.transaction_id} for {transaction.amount} BDT has status {transaction.status}."
        if transaction
        else "No matching transaction was found in the provided history."
    )
    return f"Ticket {ticket.ticket_id} appears to be a {case_type} case. {txn_text} Evidence verdict: {verdict}."


def build_next_action(case_type: CaseType, verdict: EvidenceVerdict, transaction: TransactionHistoryEntry | None) -> str:
    txn_ref = f" {transaction.transaction_id}" if transaction else ""
    if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
        return "Escalate to fraud risk, advise the customer not to share credentials, and verify only through official support channels."
    if verdict == EvidenceVerdict.INSUFFICIENT_DATA:
        return "Ask the support agent to collect non-sensitive clarification and review the account history before deciding next steps."
    if verdict == EvidenceVerdict.INCONSISTENT:
        return f"Review transaction{txn_ref} against the complaint and explain the discrepancy without promising a refund or reversal."
    if case_type == CaseType.WRONG_TRANSFER:
        return f"Send transaction{txn_ref} to dispute resolution for verification and possible recovery workflow eligibility review."
    if case_type == CaseType.PAYMENT_FAILED:
        return f"Check transaction{txn_ref} status and reconcile balance deduction before advising on any eligible reversal."
    if case_type == CaseType.DUPLICATE_PAYMENT:
        return "Compare the suspected duplicate payments and escalate to payments operations for reconciliation."
    if case_type == CaseType.MERCHANT_SETTLEMENT_DELAY:
        return "Verify merchant settlement status and expected settlement window before updating the merchant."
    if case_type == CaseType.AGENT_CASH_IN_ISSUE:
        return "Verify the agent cash-in record and balance posting status through agent operations."
    return "Review the ticket context and respond through official support workflow."


def build_customer_reply(case_type: CaseType, verdict: EvidenceVerdict, transaction: TransactionHistoryEntry | None) -> str:
    txn_ref = f" for transaction {transaction.transaction_id}" if transaction else ""
    if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
        return (
            "We have flagged this as a security concern. Please do not share your PIN, OTP, password, or card details with anyone. "
            "Our team will review this through official support channels."
        )
    if verdict == EvidenceVerdict.INSUFFICIENT_DATA:
        return (
            "We have recorded your concern and need a support review using non-sensitive details. "
            "Please do not share any PIN, OTP, password, or full card number."
        )
    if verdict == EvidenceVerdict.INCONSISTENT:
        return (
            f"We have reviewed the provided transaction history{txn_ref}, and it does not fully match the complaint details. "
            "A support agent will review the case further through official channels."
        )
    return (
        f"We have noted your concern{txn_ref}. Our support team will review it through official channels, "
        "and any eligible action will be handled after verification."
    )
