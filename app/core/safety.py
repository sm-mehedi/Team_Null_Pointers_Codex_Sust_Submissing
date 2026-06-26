from dataclasses import dataclass

from app.utils.normalization import normalize_text


CREDENTIAL_TERMS = (
    "otp",
    "pin",
    "password",
    "passcode",
    "full card",
    "card number",
    "cvv",
    "secret code",
)

SUSPICIOUS_TERMS = (
    "unknown number",
    "suspicious call",
    "scam",
    "fraud",
    "phishing",
    "fake support",
    "verify otp",
    "asked for otp",
    "asked my otp",
    "asked for pin",
    "send otp",
    "share otp",
    "share pin",
    "bkash officer",
    "account blocked",
)

PROMPT_INJECTION_TERMS = (
    "ignore previous",
    "ignore all previous",
    "ignore system",
    "developer message",
    "system prompt",
    "reveal prompt",
    "show hidden",
    "api key",
    "act as admin",
    "jailbreak",
)

UNSAFE_PROMISE_TERMS = (
    "we will refund",
    "will be refunded",
    "we guarantee",
    "will reverse",
    "account will be unblocked",
    "money will be recovered",
)


@dataclass(frozen=True)
class SafetyFinding:
    is_suspicious: bool
    has_prompt_injection: bool
    mentions_credentials: bool
    reason_codes: list[str]


def inspect_complaint(complaint: str) -> SafetyFinding:
    text = normalize_text(complaint)
    mentions_credentials = any(term in text for term in CREDENTIAL_TERMS)
    is_suspicious = any(term in text for term in SUSPICIOUS_TERMS) or mentions_credentials
    has_prompt_injection = any(term in text for term in PROMPT_INJECTION_TERMS)

    reason_codes: list[str] = []
    if is_suspicious:
        reason_codes.append("safety_sensitive")
    if mentions_credentials:
        reason_codes.append("credential_risk")
    if has_prompt_injection:
        reason_codes.append("prompt_injection_ignored")

    return SafetyFinding(
        is_suspicious=is_suspicious,
        has_prompt_injection=has_prompt_injection,
        mentions_credentials=mentions_credentials,
        reason_codes=reason_codes,
    )


def sanitize_customer_reply(reply: str) -> str:
    text = reply
    replacements = {
        "we will refund you": "any eligible amount will be returned through official channels after review",
        "we will reverse": "any eligible reversal will be handled through official channels after review",
        "share your otp": "do not share your OTP",
        "share your pin": "do not share your PIN",
        "send your password": "do not share your password",
    }
    lowered = text.lower()
    for unsafe, safe in replacements.items():
        if unsafe in lowered:
            text = text.replace(unsafe, safe)
            text = text.replace(unsafe.title(), safe)
            lowered = text.lower()

    if any(term in lowered for term in UNSAFE_PROMISE_TERMS):
        return (
            "Your concern has been recorded for review. Any eligible action will be handled "
            "through official support channels after verification."
        )
    return text
