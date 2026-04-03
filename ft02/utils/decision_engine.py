"""
Bank Decision Simulator

Simulates a bank's loan approval decision based on credit score,
fraud probability, and key business features.

Outputs: APPROVE / REVIEW / REJECT with detailed reasons.
"""

from utils.constants import DECISION_THRESHOLDS


def make_loan_decision(credit_score: int, fraud_probability: float,
                       features: dict) -> dict:
    """
    Simulate a bank's loan decision.

    Args:
        credit_score: Score between 300-900
        fraud_probability: Probability 0-1
        features: Dict containing business features for reason generation

    Returns:
        Dict with 'decision', 'reasons', and 'recommended_loan_amount'
    """
    thresholds = DECISION_THRESHOLDS
    reasons = []
    decision = "REVIEW"

    # ── Hard REJECT conditions ──────────────────────────────────────────────
    reject = False

    if fraud_probability >= thresholds["reject_min_fraud"]:
        reject = True
        reasons.append(
            f"High fraud probability ({fraud_probability:.2f}) exceeds threshold "
            f"({thresholds['reject_min_fraud']})"
        )

    if credit_score <= thresholds["reject_max_score"]:
        reject = True
        reasons.append(
            f"Credit score ({credit_score}) below minimum threshold "
            f"({thresholds['reject_max_score']})"
        )

    # Check for severe red flags
    loan_defaults = features.get("loan_defaults", 0)
    if loan_defaults >= 3:
        reject = True
        reasons.append(f"Multiple loan defaults ({loan_defaults}) in history")

    gst_cancellation = features.get("gst_cancellation_history", False)
    if gst_cancellation and fraud_probability > 0.5:
        reject = True
        reasons.append("GST registration cancelled with elevated fraud risk")

    if reject:
        return {
            "decision": "REJECT",
            "reasons": reasons,
            "recommended_loan_amount": 0,
            "confidence": min(0.95, 0.5 + fraud_probability * 0.5),
        }

    # ── APPROVE conditions ──────────────────────────────────────────────────
    approve = True
    approve_reasons = []

    if credit_score < thresholds["approve_min_score"]:
        approve = False
        reasons.append(
            f"Credit score ({credit_score}) below approval threshold "
            f"({thresholds['approve_min_score']})"
        )
    else:
        approve_reasons.append(f"Strong credit score ({credit_score})")

    if fraud_probability > thresholds["approve_max_fraud"]:
        approve = False
        reasons.append(
            f"Fraud probability ({fraud_probability:.2f}) above comfort level "
            f"({thresholds['approve_max_fraud']})"
        )
    else:
        approve_reasons.append(
            f"Low fraud probability ({fraud_probability:.2f})"
        )

    # Additional positive signals
    sales_volatility = features.get("sales_volatility", 0.5)
    if sales_volatility > 0.4:
        approve = False
        reasons.append(f"Unstable sales pattern (volatility: {sales_volatility:.2f})")
    else:
        approve_reasons.append("Stable sales pattern")

    customer_concentration = features.get("dependency_on_single_customer", 0.5)
    if customer_concentration > 0.6:
        reasons.append(
            f"High customer concentration ({customer_concentration:.0%} revenue "
            f"from single customer)"
        )
        if customer_concentration > 0.8:
            approve = False

    repayment_ratio = features.get("repayment_ratio", 0.8)
    if repayment_ratio < 0.7:
        approve = False
        reasons.append(
            f"Poor repayment history (ratio: {repayment_ratio:.2f})"
        )

    if approve:
        loan_amount = _calculate_loan_amount(credit_score, features)
        return {
            "decision": "APPROVE",
            "reasons": approve_reasons + reasons,
            "recommended_loan_amount": loan_amount,
            "confidence": min(0.95, 0.3 + (credit_score - 300) / 600 * 0.5),
        }

    # ── REVIEW (everything else) ────────────────────────────────────────────
    loan_amount = _calculate_loan_amount(credit_score, features) // 2
    review_reasons = reasons if reasons else ["Manual review required — borderline case"]

    return {
        "decision": "REVIEW",
        "reasons": review_reasons,
        "recommended_loan_amount": loan_amount,
        "confidence": 0.5,
    }


def _calculate_loan_amount(credit_score: int, features: dict) -> int:
    """Calculate recommended loan amount based on score and turnover."""
    estimated_turnover = features.get("estimated_turnover", 1000000)

    # Base: percentage of turnover
    if credit_score >= 800:
        multiplier = 0.50
    elif credit_score >= 750:
        multiplier = 0.35
    elif credit_score >= 700:
        multiplier = 0.25
    elif credit_score >= 650:
        multiplier = 0.15
    elif credit_score >= 550:
        multiplier = 0.10
    else:
        multiplier = 0.05

    amount = int(estimated_turnover * multiplier)

    # Cap at reasonable limits
    amount = max(25000, min(amount, 5000000))

    # Round to nearest 10000
    amount = round(amount / 10000) * 10000

    return amount


def format_decision_summary(decision_result: dict, business_name: str) -> str:
    """Format decision result as a human-readable summary."""
    d = decision_result
    lines = [
        f"═══ LOAN DECISION: {business_name} ═══",
        f"",
        f"  Decision:          {d['decision']}",
        f"  Recommended Loan:  ₹{d['recommended_loan_amount']:,}",
        f"  Confidence:        {d['confidence']:.0%}",
        f"",
        f"  Reasons:",
    ]
    for reason in d["reasons"]:
        lines.append(f"    • {reason}")

    lines.append("═" * 50)
    return "\n".join(lines)
