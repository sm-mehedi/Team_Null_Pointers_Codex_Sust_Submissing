from app.models.enums import CaseType, Department


def route_department(case_type: CaseType) -> Department:
    if case_type == CaseType.WRONG_TRANSFER:
        return Department.DISPUTE_RESOLUTION
    if case_type in {CaseType.PAYMENT_FAILED, CaseType.DUPLICATE_PAYMENT}:
        return Department.PAYMENTS_OPS
    if case_type == CaseType.MERCHANT_SETTLEMENT_DELAY:
        return Department.MERCHANT_OPERATIONS
    if case_type == CaseType.AGENT_CASH_IN_ISSUE:
        return Department.AGENT_OPERATIONS
    if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
        return Department.FRAUD_RISK
    if case_type == CaseType.REFUND_REQUEST:
        return Department.CUSTOMER_SUPPORT
    return Department.CUSTOMER_SUPPORT
