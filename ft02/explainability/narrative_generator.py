"""
Natural Language Narrative Generator

Converts SHAP values and feature data into human-readable explanations
for credit scores and fraud probabilities.
"""


# ─── Feature Name Mappings ──────────────────────────────────────────────────────
CREDIT_FEATURE_NAMES = {
    "repayment_ratio":          "Loan repayment history",
    "loan_burden_ratio":        "Outstanding loan burden",
    "gst_compliance_score":     "GST filing compliance",
    "late_filings_count":       "Late GST filings",
    "months_not_filed":         "Months without GST filing",
    "gst_cancellation":         "GST registration cancelled",
    "turnover_stability":       "Turnover stability",
    "sales_volatility":         "Sales volatility",
    "growth_rate":              "Revenue growth rate",
    "ps_consistency":           "Purchase-sales consistency",
    "purchase_to_sales_ratio":  "Purchase to sales ratio",
    "sector_risk":              "Industry sector risk",
    "vendor_diversification":   "Vendor diversification",
    "customer_diversification": "Customer diversification",
    "dependency_on_single_customer": "Single customer dependency",
    "business_age":             "Business maturity",
    "age_score":                "Business age score",
    "estimated_turnover":       "Estimated annual turnover",
    "previous_loans_count":     "Number of previous loans",
    "loan_defaults":            "Loan defaults",
}

FRAUD_FEATURE_NAMES = {
    "spike_count":              "Sudden revenue spikes",
    "max_spike_pct":            "Maximum revenue spike",
    "sales_volatility":         "Sales pattern volatility",
    "ps_mismatch":              "Purchase-sales mismatch",
    "ps_ratio":                 "Purchase to sales ratio",
    "itc_anomaly":              "Input Tax Credit anomaly",
    "gst_cancellation":         "GST cancellation history",
    "late_filings":             "Late GST filing count",
    "months_not_filed":         "Filing gaps (months)",
    "multi_registration":       "Multiple GST registrations",
    "filing_gap_score":         "Filing gap severity",
    "circular_trade_flag":      "Circular vendor trading",
    "circular_trade_count":     "Circular trade patterns",
    "network_density":          "Network density anomaly",
    "customer_concentration":   "Customer revenue concentration",
    "dependency_single_cust":   "Single customer dependency",
    "vendor_count":             "Number of vendors",
    "customer_count":           "Number of customers",
    "loan_defaults":            "Loan default history",
    "default_ratio":            "Loan default ratio",
    "business_age":             "Business age (years)",
    "sector_risk":              "Industry sector risk",
}


def generate_credit_narrative(business: dict, shap_result: dict) -> list:
    """
    Generate natural-language credit score explanations.

    Args:
        business: Complete business dictionary
        shap_result: Output from explain_credit_score()

    Returns:
        List of explanation strings
    """
    explanations = []
    credit_score = business.get("credit_score", 0)
    features = business.get("_credit_features", {})

    # Header
    if credit_score >= 750:
        explanations.append(f"Credit score of {credit_score} indicates STRONG creditworthiness.")
    elif credit_score >= 600:
        explanations.append(f"Credit score of {credit_score} indicates MODERATE creditworthiness.")
    else:
        explanations.append(f"Credit score of {credit_score} indicates WEAK creditworthiness.")

    # Positive factors
    positives = shap_result.get("top_positive_factors", [])
    if positives:
        explanations.append("\nFactors supporting the credit score:")
        for feat, value in positives[:4]:
            readable = CREDIT_FEATURE_NAMES.get(feat, feat.replace("_", " ").title())
            feat_val = features.get(feat, "")
            if isinstance(feat_val, float):
                feat_val_str = f" ({feat_val:.2f})"
            elif isinstance(feat_val, int):
                feat_val_str = f" ({feat_val})"
            else:
                feat_val_str = ""
            explanations.append(f"  + {readable}{feat_val_str}")

    # Negative factors
    negatives = shap_result.get("top_negative_factors", [])
    if negatives:
        explanations.append("\nFactors reducing the credit score:")
        for feat, value in negatives[:4]:
            readable = CREDIT_FEATURE_NAMES.get(feat, feat.replace("_", " ").title())
            feat_val = features.get(feat, "")

            # Add specific detail
            detail = _get_credit_detail(feat, features)
            if detail:
                explanations.append(f"  [!] {readable}: {detail}")
            else:
                explanations.append(f"  [!] {readable}")

    return explanations


def generate_fraud_narrative(business: dict, shap_result: dict) -> list:
    """
    Generate natural-language fraud risk explanations.

    Args:
        business: Complete business dictionary
        shap_result: Output from explain_fraud_prediction()

    Returns:
        List of explanation strings
    """
    explanations = []
    fraud_prob = business.get("fraud_probability", 0)
    features = business.get("_fraud_features", {})

    # Header
    if fraud_prob >= 0.7:
        explanations.append(f"Fraud probability of {fraud_prob:.0%} - HIGH RISK")
    elif fraud_prob >= 0.4:
        explanations.append(f"Fraud probability of {fraud_prob:.0%} - MODERATE RISK")
    else:
        explanations.append(f"Fraud probability of {fraud_prob:.0%} - LOW RISK")

    # Risk factors
    risk_factors = shap_result.get("top_risk_factors", [])
    if risk_factors:
        explanations.append("\nFraud risk factors:")
        for feat, value in risk_factors[:5]:
            readable = FRAUD_FEATURE_NAMES.get(feat, feat.replace("_", " ").title())
            detail = _get_fraud_detail(feat, features, business)
            if detail:
                explanations.append(f"  [!] {readable}: {detail}")
            else:
                explanations.append(f"  [!] {readable}")

    return explanations


def _get_credit_detail(feature: str, features: dict) -> str:
    """Generate specific detail string for a credit feature."""
    val = features.get(feature)
    if val is None:
        return ""

    detail_map = {
        "late_filings_count": f"{val} late filings in observation period",
        "months_not_filed": f"{val} months without filing",
        "sales_volatility": f"coefficient of variation: {val:.2f}",
        "loan_defaults": f"{val} recorded defaults",
        "dependency_on_single_customer": f"{val:.0%} revenue from single customer",
        "growth_rate": f"{'positive' if val > 0 else 'negative'} at {val:.1%}/month",
        "sector_risk": f"industry risk level: {val:.0%}",
    }

    return detail_map.get(feature, "")


def _get_fraud_detail(feature: str, features: dict, business: dict) -> str:
    """Generate specific detail string for a fraud feature."""
    val = features.get(feature)
    if val is None:
        return ""

    sales_data = business.get("sales_data", {})
    spikes = sales_data.get("sudden_sales_spikes", [])

    detail_map = {
        "spike_count": f"{val} sudden spikes detected",
        "max_spike_pct": f"maximum spike of {val:.0%}",
        "circular_trade_count": f"{val} circular trading patterns",
        "ps_mismatch": f"ratio deviation of {val:.2f} from normal range",
        "gst_cancellation": "registration was cancelled",
        "late_filings": f"{val} late filings",
        "months_not_filed": f"GST not filed for {val} months",
        "dependency_single_cust": f"{val:.0%} revenue from single customer",
    }

    result = detail_map.get(feature, "")

    # Add spike month details
    if feature == "spike_count" and spikes:
        months_str = ", ".join([f"Month {m+1}" for m in spikes[:3]])
        result += f" ({months_str})"

    return result


def compile_all_explanations(business: dict,
                             credit_shap: dict,
                             fraud_shap: dict) -> list:
    """
    Compile all explanations for a business into a single list.

    Args:
        business: Complete business dictionary
        credit_shap: Credit SHAP result
        fraud_shap: Fraud SHAP result

    Returns:
        Combined list of explanation strings
    """
    credit_narr = generate_credit_narrative(business, credit_shap)
    fraud_narr = generate_fraud_narrative(business, fraud_shap)

    all_explanations = credit_narr + ["\n---\n"] + fraud_narr
    return all_explanations
