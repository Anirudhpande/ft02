"""
Fraud Feature Engineering

Extracts fraud-specific features from business data for
the fraud detection model. Focuses on anomaly indicators
and behavioral red flags.
"""

import numpy as np


def build_fraud_features(business: dict) -> dict:
    """
    Extract fraud-specific features from a business record.

    Args:
        business: Complete business dictionary

    Returns:
        Dict of numerical features for fraud detection model
    """
    sales = business.get("sales_data", {})
    purchase = business.get("purchase_data", {})
    gst = business.get("gst_behavior", {})
    network = business.get("network_data", {})
    loan = business.get("loan_history", {})
    identity = business.get("business_identity", {})

    monthly_sales = sales.get("monthly_sales", [])

    # ── Spike Analysis ──────────────────────────────────────────────────────
    spike_count = len(sales.get("sudden_sales_spikes", []))

    max_spike_pct = 0.0
    if len(monthly_sales) > 1:
        for i in range(1, len(monthly_sales)):
            if monthly_sales[i - 1] > 0:
                pct = (monthly_sales[i] - monthly_sales[i - 1]) / monthly_sales[i - 1]
                max_spike_pct = max(max_spike_pct, pct)

    # ── Sales Volatility ────────────────────────────────────────────────────
    sales_volatility = sales.get("sales_volatility", 0.0)

    # ── Purchase-Sales Mismatch ─────────────────────────────────────────────
    ps_ratio = purchase.get("purchase_to_sales_ratio", 0.65)

    # Deviation from expected range (0.4-0.85)
    if ps_ratio < 0.4:
        ps_mismatch = 0.4 - ps_ratio
    elif ps_ratio > 0.85:
        ps_mismatch = ps_ratio - 0.85
    else:
        ps_mismatch = 0.0

    # ── ITC Anomaly ─────────────────────────────────────────────────────────
    monthly_purchases = purchase.get("monthly_purchases", [])
    itc_claimed = purchase.get("input_tax_credit_claimed", [])

    itc_anomaly = 0.0
    if monthly_purchases and itc_claimed and sum(monthly_purchases) > 0:
        expected_itc_rate = 0.15  # Approximate average GST rate
        actual_itc_rate = sum(itc_claimed) / max(sum(monthly_purchases), 1)
        itc_anomaly = max(0, actual_itc_rate - expected_itc_rate * 1.3)

    # ── GST Red Flags ───────────────────────────────────────────────────────
    gst_cancellation = 1 if gst.get("gst_cancellation_history", False) else 0
    late_filings = gst.get("late_filings_count", 0)
    months_not_filed = gst.get("months_not_filed", 0)
    multi_reg = 1 if gst.get("multiple_gst_registrations", False) else 0

    # Filing gap severity
    filing_gap_score = min(1.0, months_not_filed / 6.0 + late_filings / 12.0)

    # ── Network Anomalies ───────────────────────────────────────────────────
    circular_count = len(network.get("circular_trades", []))
    circular_trade_flag = 1 if circular_count > 0 else 0

    vendor_count = network.get("vendor_count", 5)
    customer_count = network.get("customer_count", 10)
    total_edges = network.get("total_edges", 10)
    total_nodes = network.get("total_nodes", 10)

    # Network density (suspicious if very dense for small networks)
    if total_nodes > 1:
        max_edges = total_nodes * (total_nodes - 1)
        network_density = total_edges / max(max_edges, 1)
    else:
        network_density = 0.0

    concentration = network.get("customer_concentration_ratio", 0.5)
    dependency = network.get("dependency_on_single_customer", 0.5)

    # ── Loan Behavior ───────────────────────────────────────────────────────
    loan_defaults = loan.get("loan_defaults", 0)
    total_loans = loan.get("previous_loans_count", 0)
    default_ratio = loan_defaults / max(total_loans, 1)

    # ── Business Profile ────────────────────────────────────────────────────
    business_age = identity.get("business_age", 3)
    sector_risk = identity.get("risk_sector_score", 5) / 10.0

    # ── Compile features ────────────────────────────────────────────────────
    features = {
        "spike_count":              int(spike_count),
        "max_spike_pct":            round(float(max_spike_pct), 4),
        "sales_volatility":         round(float(sales_volatility), 4),
        "ps_mismatch":              round(float(ps_mismatch), 4),
        "ps_ratio":                 round(float(ps_ratio), 4),
        "itc_anomaly":              round(float(itc_anomaly), 4),
        "gst_cancellation":         int(gst_cancellation),
        "late_filings":             int(late_filings),
        "months_not_filed":         int(months_not_filed),
        "multi_registration":       int(multi_reg),
        "filing_gap_score":         round(float(filing_gap_score), 4),
        "circular_trade_flag":      int(circular_trade_flag),
        "circular_trade_count":     int(circular_count),
        "network_density":          round(float(network_density), 6),
        "customer_concentration":   round(float(concentration), 4),
        "dependency_single_cust":   round(float(dependency), 4),
        "vendor_count":             int(vendor_count),
        "customer_count":           int(customer_count),
        "loan_defaults":            int(loan_defaults),
        "default_ratio":            round(float(default_ratio), 4),
        "business_age":             int(business_age),
        "sector_risk":              round(float(sector_risk), 4),
    }

    return features


def get_fraud_feature_columns() -> list:
    """Return ordered list of fraud feature column names."""
    return [
        "spike_count", "max_spike_pct", "sales_volatility",
        "ps_mismatch", "ps_ratio", "itc_anomaly",
        "gst_cancellation", "late_filings", "months_not_filed",
        "multi_registration", "filing_gap_score",
        "circular_trade_flag", "circular_trade_count", "network_density",
        "customer_concentration", "dependency_single_cust",
        "vendor_count", "customer_count",
        "loan_defaults", "default_ratio",
        "business_age", "sector_risk",
    ]
