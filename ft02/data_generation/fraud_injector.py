"""
Fraud Pattern Injector

Determines which businesses are fraudulent and injects
realistic anomaly patterns across their data. Controls the
fraud_label assignment and ensures ~18% fraud rate.
"""

import numpy as np
from utils.constants import FRAUD_RATE


def assign_fraud_label(business_idx: int, total_businesses: int) -> bool:
    """
    Determine if a business should be fraudulent.

    Uses controlled randomization to maintain target fraud rate.

    Args:
        business_idx: Index of business being generated
        total_businesses: Total number of businesses

    Returns:
        True if business should be fraudulent
    """
    return np.random.random() < FRAUD_RATE


def inject_fraud_indicators(business_data: dict) -> dict:
    """
    Analyze a fraudulent business's data and compile fraud indicators.

    This doesn't modify data (fraud patterns are injected during generation),
    but computes summary fraud indicators from the generated data.

    Args:
        business_data: Complete business dictionary

    Returns:
        Dict with fraud indicator flags and descriptions
    """
    indicators = []

    sales_data = business_data.get("sales_data", {})
    purchase_data = business_data.get("purchase_data", {})
    gst_behavior = business_data.get("gst_behavior", {})
    network_data = business_data.get("network_data", {})
    loan_history = business_data.get("loan_history", {})

    # ── Revenue spike detection ─────────────────────────────────────────────
    spikes = sales_data.get("sudden_sales_spikes", [])
    monthly_sales = sales_data.get("monthly_sales", [])

    if spikes and len(monthly_sales) > 1:
        for spike_month in spikes:
            if spike_month > 0 and spike_month < len(monthly_sales):
                prev = monthly_sales[spike_month - 1]
                current = monthly_sales[spike_month]
                if prev > 0:
                    pct_change = ((current - prev) / prev) * 100
                    indicators.append({
                        "type": "revenue_spike",
                        "description": f"Sudden sales spike of {pct_change:.0f}% in month {spike_month + 1}",
                        "severity": "high" if pct_change > 300 else "medium",
                    })

    # ── Purchase-sales mismatch ─────────────────────────────────────────────
    ps_ratio = purchase_data.get("purchase_to_sales_ratio", 0.65)
    if ps_ratio < 0.20:
        indicators.append({
            "type": "purchase_sales_mismatch",
            "description": f"Abnormally low purchase-to-sales ratio ({ps_ratio:.2f})",
            "severity": "high",
        })
    elif ps_ratio > 1.0:
        indicators.append({
            "type": "purchase_sales_mismatch",
            "description": f"Purchases exceed sales (ratio: {ps_ratio:.2f})",
            "severity": "high",
        })

    # ── GST irregularities ──────────────────────────────────────────────────
    if gst_behavior.get("gst_cancellation_history", False):
        indicators.append({
            "type": "gst_cancellation",
            "description": "GST registration cancelled — shell company risk",
            "severity": "high",
        })

    late_count = gst_behavior.get("late_filings_count", 0)
    if late_count >= 6:
        indicators.append({
            "type": "gst_non_compliance",
            "description": f"Excessive late GST filings ({late_count} late filings)",
            "severity": "medium",
        })

    months_not_filed = gst_behavior.get("months_not_filed", 0)
    if months_not_filed >= 3:
        indicators.append({
            "type": "gst_non_filing",
            "description": f"GST not filed for {months_not_filed} months",
            "severity": "high",
        })

    if gst_behavior.get("multiple_gst_registrations", False):
        indicators.append({
            "type": "multiple_registrations",
            "description": "Multiple GST registrations detected",
            "severity": "medium",
        })

    # ── Network anomalies ───────────────────────────────────────────────────
    circular = network_data.get("circular_trades", [])
    if circular:
        indicators.append({
            "type": "circular_trading",
            "description": f"Circular vendor trading detected ({len(circular)} patterns)",
            "severity": "critical",
        })

    concentration = network_data.get("dependency_on_single_customer", 0)
    if concentration > 0.8:
        indicators.append({
            "type": "customer_dependency",
            "description": f"Extreme dependency on single customer ({concentration:.0%} revenue)",
            "severity": "medium",
        })

    # ── Loan defaults ───────────────────────────────────────────────────────
    defaults = loan_history.get("loan_defaults", 0)
    if defaults >= 2:
        indicators.append({
            "type": "loan_defaults",
            "description": f"Multiple loan defaults ({defaults} defaults)",
            "severity": "high",
        })

    return {
        "fraud_indicators": indicators,
        "total_red_flags": len(indicators),
        "max_severity": _max_severity(indicators),
    }


def _max_severity(indicators: list) -> str:
    """Return the maximum severity from a list of indicators."""
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    if not indicators:
        return "none"
    max_sev = max(indicators, key=lambda x: severity_order.get(x["severity"], 0))
    return max_sev["severity"]
