"""
GST Behavior Generator

Generates realistic GST filing behavior for businesses including
filing frequency, late filings, months not filed, cancellation history,
and multiple registrations. Parameters are correlated with fraud label.
"""

import numpy as np
from utils.constants import GST_PARAMS


def generate_gst_behavior(business_age: int, estimated_turnover: float,
                          is_fraud: bool = False) -> dict:
    """
    Generate GST filing behavior for a business.

    Args:
        business_age: Age of business in years
        estimated_turnover: Estimated annual turnover in INR
        is_fraud: Whether business is fraudulent

    Returns:
        Dict with GST behavior fields
    """
    params = GST_PARAMS

    # Filing frequency based on turnover (threshold ₹5 crore for monthly)
    if estimated_turnover > 50000000:
        gst_filing_frequency = "monthly"
    elif estimated_turnover > 15000000:
        gst_filing_frequency = "monthly"
    else:
        gst_filing_frequency = np.random.choice(
            ["monthly", "quarterly"],
            p=[0.6, 0.4]
        )

    # Late filings count (Poisson distribution)
    if is_fraud:
        late_lambda = params["late_filing_lambda_bad"]
    else:
        late_lambda = params["late_filing_lambda_good"]

    # Scale with business age (newer businesses file late more)
    age_factor = max(0.5, 1.5 - business_age / 10.0)
    late_filings_count = int(np.random.poisson(late_lambda * age_factor))

    # Cap at reasonable maximum (based on 36 months)
    late_filings_count = min(late_filings_count, 24)

    # Months not filed
    if is_fraud:
        months_not_filed = int(np.random.poisson(3))
        months_not_filed = min(months_not_filed, 12)
    else:
        if np.random.random() < 0.15:
            months_not_filed = int(np.random.poisson(1))
            months_not_filed = min(months_not_filed, 4)
        else:
            months_not_filed = 0

    # GST cancellation history
    if is_fraud:
        gst_cancellation_history = np.random.random() < params["cancellation_prob_bad"]
    else:
        gst_cancellation_history = np.random.random() < params["cancellation_prob_good"]

    # Multiple GST registrations
    if is_fraud:
        multiple_gst_registrations = np.random.random() < params["multi_registration_prob"] * 3
    else:
        multiple_gst_registrations = np.random.random() < params["multi_registration_prob"]

    return {
        "gst_filing_frequency": str(gst_filing_frequency),
        "late_filings_count": int(late_filings_count),
        "months_not_filed": int(months_not_filed),
        "gst_cancellation_history": bool(gst_cancellation_history),
        "multiple_gst_registrations": bool(multiple_gst_registrations),
    }
