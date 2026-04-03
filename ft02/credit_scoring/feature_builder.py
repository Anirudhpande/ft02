"""
Credit Scoring Feature Builder

Extracts ML-ready features from business JSON data for credit scoring.
Transforms raw business fields into normalized numerical features
suitable for gradient boosting models.
"""

import numpy as np
from utils.amnesty_config import is_any_amnesty_active


def build_credit_features(business: dict) -> dict:
    """
    Extract credit scoring features from a business record.

    Args:
        business: Complete business dictionary

    Returns:
        Dict of numerical features for ML model
    """
    identity = business.get("business_identity", {})
    loan = business.get("loan_history", {})
    gst = business.get("gst_behavior", {})
    sales = business.get("sales_data", {})
    purchase = business.get("purchase_data", {})
    network = business.get("network_data", {})

    # ── Repayment Features ──────────────────────────────────────────────────
    total_loans = loan.get("previous_loans_count", 0)
    defaults = loan.get("loan_defaults", 0)
    repayment_ratio = 1.0 - (defaults / max(total_loans, 1))

    outstanding = loan.get("outstanding_loans", 0)
    avg_loan_size = loan.get("average_loan_size", 0)
    loan_burden_ratio = outstanding / max(avg_loan_size, 1)

    # ── GST Compliance Features ─────────────────────────────────────────────
    late_filings = gst.get("late_filings_count", 0)
    months_not_filed = gst.get("months_not_filed", 0)
    gst_cancellation = 1 if gst.get("gst_cancellation_history", False) else 0
    multi_registration = 1 if gst.get("multiple_gst_registrations", False) else 0

    # ── GST Amnesty Adjustment ──────────────────────────────────────────────
    # When the government declares an amnesty quarter, late filings during
    # that window must NOT penalise the MSME.  We dynamically zero out the
    # late-filing contribution to the compliance score (and clamp the raw
    # feature values fed to the ML model) so that the trained model sees
    # them as benign — without retraining.
    amnesty_active = is_any_amnesty_active()
    if amnesty_active:
        late_filings_for_scoring = 0
        months_not_filed_for_scoring = 0
    else:
        late_filings_for_scoring = late_filings
        months_not_filed_for_scoring = months_not_filed

    # Compliance score (0-1, higher is better)
    gst_compliance_score = max(0, 1.0 - (late_filings_for_scoring * 0.05)
                               - (months_not_filed_for_scoring * 0.1)
                               - (gst_cancellation * 0.3) - (multi_registration * 0.1))

    # ── Turnover Stability ──────────────────────────────────────────────────
    monthly_sales = sales.get("monthly_sales", [])
    if len(monthly_sales) > 1:
        sales_arr = np.array(monthly_sales)
        mean_sales = np.mean(sales_arr)
        std_sales = np.std(sales_arr)
        sales_cv = std_sales / max(mean_sales, 1)  # Coefficient of variation

        # Growth rate (linear regression slope / mean)
        t = np.arange(len(sales_arr))
        if len(t) > 1:
            slope = np.polyfit(t, sales_arr, 1)[0]
            growth_rate = slope / max(mean_sales, 1)
        else:
            growth_rate = 0.0
    else:
        sales_cv = 0.5
        growth_rate = 0.0
        mean_sales = 0.0

    turnover_stability = max(0, 1.0 - sales_cv)

    # ── Purchase-Sales Consistency ──────────────────────────────────────────
    ps_ratio = purchase.get("purchase_to_sales_ratio", 0.65)
    # Ideal ratio is 0.5-0.8; penalize deviations
    if 0.4 <= ps_ratio <= 0.85:
        ps_consistency = 1.0
    elif ps_ratio < 0.4:
        ps_consistency = max(0, ps_ratio / 0.4)
    else:
        ps_consistency = max(0, 1.0 - (ps_ratio - 0.85) / 0.5)

    # ── Sector Risk ─────────────────────────────────────────────────────────
    sector_risk = identity.get("risk_sector_score", 5)
    sector_risk_normalized = sector_risk / 10.0

    # ── Network Features ────────────────────────────────────────────────────
    vendor_count = network.get("vendor_count", 5)
    customer_count = network.get("customer_count", 10)
    concentration = network.get("customer_concentration_ratio", 0.5)
    dependency = network.get("dependency_on_single_customer", 0.5)

    # Vendor diversification (higher is better)
    vendor_diversification = min(1.0, vendor_count / 20.0)

    # Customer diversification (lower concentration is better)
    customer_diversification = 1.0 - concentration

    # ── Business Maturity ───────────────────────────────────────────────────
    business_age = identity.get("business_age", 3)
    age_score = min(1.0, business_age / 10.0)

    # ── Estimated Turnover ──────────────────────────────────────────────────
    estimated_turnover = sales.get("estimated_turnover", 0)

    # ── Compile feature vector ──────────────────────────────────────────────
    features = {
        "repayment_ratio":          round(float(repayment_ratio), 4),
        "loan_burden_ratio":        round(float(loan_burden_ratio), 4),
        "gst_compliance_score":     round(float(gst_compliance_score), 4),
        "late_filings_count":       int(late_filings_for_scoring),
        "months_not_filed":         int(months_not_filed_for_scoring),
        "gst_cancellation":         int(gst_cancellation),
        "turnover_stability":       round(float(turnover_stability), 4),
        "sales_volatility":         round(float(sales_cv), 4),
        "growth_rate":              round(float(growth_rate), 6),
        "ps_consistency":           round(float(ps_consistency), 4),
        "purchase_to_sales_ratio":  round(float(ps_ratio), 4),
        "sector_risk":              round(float(sector_risk_normalized), 4),
        "vendor_diversification":   round(float(vendor_diversification), 4),
        "customer_diversification": round(float(customer_diversification), 4),
        "dependency_on_single_customer": round(float(dependency), 4),
        "business_age":             int(business_age),
        "age_score":                round(float(age_score), 4),
        "estimated_turnover":       round(float(estimated_turnover), 2),
        "previous_loans_count":     int(total_loans),
        "loan_defaults":            int(defaults),
        "amnesty_applied":          1 if amnesty_active else 0,
    }

    return features


def get_feature_columns() -> list:
    """Return ordered list of feature column names for ML models."""
    return [
        "repayment_ratio",
        "loan_burden_ratio",
        "gst_compliance_score",
        "late_filings_count",
        "months_not_filed",
        "gst_cancellation",
        "turnover_stability",
        "sales_volatility",
        "growth_rate",
        "ps_consistency",
        "purchase_to_sales_ratio",
        "sector_risk",
        "vendor_diversification",
        "customer_diversification",
        "dependency_on_single_customer",
        "business_age",
        "age_score",
        "estimated_turnover",
        "previous_loans_count",
        "loan_defaults",
    ]
