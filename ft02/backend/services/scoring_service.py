"""
Credit Scoring Service

Rule-based scoring engine for MSME credit assessment.
Base score: 650. Adjustments based on GST consistency,
UPI activity, shipment volume, and filing delays.
"""


def calculate_credit_score(features: dict) -> dict:
    """
    Calculate a credit score and generate human-readable reasons.

    Args:
        features: dict with keys avg_filing_delay, total_upi_volume,
                  shipment_count, avg_transaction_value, transaction_count

    Returns:
        dict with 'score' (int) and 'reasons' (list of str)
    """

    score = 650  # base score
    reasons = []

    # 1. GST Filing Consistency
    avg_delay = features.get("avg_filing_delay", 0)

    if avg_delay <= 0:
        score += 50
        reasons.append("Consistent GST filings with no delays")
    elif avg_delay <= 2:
        score += 20
        reasons.append("GST filings mostly on time")
    else:
        score -= 40
        reasons.append("Frequent GST filing delays detected")

    # 2. UPI Transaction Volume
    total_volume = features.get("total_upi_volume", 0)

    if total_volume > 1000000:
        score += 50
        reasons.append("High UPI transaction volume indicating strong cash flow")
    elif total_volume > 500000:
        score += 30
        reasons.append("Moderate UPI transaction volume")
    else:
        score -= 20
        reasons.append("Low UPI transaction volume")

    # 3. Transaction Count
    txn_count = features.get("transaction_count", 0)

    if txn_count > 150:
        score += 40
        reasons.append("High number of business transactions")
    elif txn_count > 50:
        score += 15
        reasons.append("Moderate transaction activity")
    else:
        score -= 20
        reasons.append("Low transaction activity")

    # 4. Average Transaction Value
    avg_txn = features.get("avg_transaction_value", 0)

    if avg_txn > 5000:
        score += 20
        reasons.append("Strong average transaction value")
    elif avg_txn > 2000:
        score += 10
        reasons.append("Moderate average transaction value")

    # 5. Shipment Activity
    shipment_count = features.get("shipment_count", 0)

    if shipment_count > 15:
        score += 40
        reasons.append("Stable shipment activity indicating active operations")
    elif shipment_count > 5:
        score += 20
        reasons.append("Moderate shipment activity")
    else:
        score -= 15
        reasons.append("Low shipment activity")

    # Normalize to 300–900 range
    score = max(300, min(score, 900))

    # Keep top 5 positive reasons first, then negatives
    positive = [r for r in reasons if not r.startswith(("Low", "Frequent"))]
    negative = [r for r in reasons if r.startswith(("Low", "Frequent"))]
    top_reasons = (positive + negative)[:5]

    return {
        "score": score,
        "reasons": top_reasons
    }


def classify_risk_band(score: int) -> str:
    """Classify score into a risk band."""

    if score >= 750:
        return "LOW"
    elif score >= 650:
        return "MEDIUM"
    elif score >= 500:
        return "HIGH"
    else:
        return "VERY HIGH"


def recommend_loan_amount(score: int) -> int:
    """Recommend loan amount based on credit score."""

    if score >= 800:
        return 1000000
    elif score >= 750:
        return 750000
    elif score >= 700:
        return 500000
    elif score >= 650:
        return 300000
    elif score >= 500:
        return 100000
    else:
        return 25000
