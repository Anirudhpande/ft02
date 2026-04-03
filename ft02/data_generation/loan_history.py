"""
Loan History Generator

Generates realistic previous loan history for businesses using
probabilistic distributions. Loan counts follow Poisson distribution,
sizes follow GMM, and defaults are correlated with business risk profile.
"""

import numpy as np
from utils.constants import LOAN_PARAMS
from synthetic_models.gmm_engine import create_loan_size_sampler


# Pre-build loan size sampler
_loan_sampler = create_loan_size_sampler(
    LOAN_PARAMS["size_mean"],
    LOAN_PARAMS["size_std"],
)


def generate_loan_history(business_age: int, sector_risk: int,
                          is_fraud: bool = False) -> dict:
    """
    Generate previous loan history for a business.

    Args:
        business_age: Age of business in years
        sector_risk: Sector risk score (1-10)
        is_fraud: Whether business is fraudulent

    Returns:
        Dict with loan history fields
    """
    # Number of previous loans (Poisson, scaled by age)
    age_factor = min(business_age / 5.0, 2.0)
    lam = LOAN_PARAMS["count_lambda"] * age_factor
    previous_loans_count = int(np.random.poisson(lam))
    previous_loans_count = min(previous_loans_count, 10)

    if previous_loans_count == 0:
        return {
            "previous_loans_count": 0,
            "loan_repayment_history": [],
            "loan_defaults": 0,
            "outstanding_loans": 0,
            "average_loan_size": 0,
        }

    # Generate individual loan records
    loan_sizes = _loan_sampler.sample(previous_loans_count)
    loan_sizes = [round(float(s), -3) for s in loan_sizes]  # Round to nearest 1000

    # Determine default rate based on risk profile
    if is_fraud:
        default_rate = LOAN_PARAMS["default_rate_bad"]
    else:
        # Scale default rate with sector risk
        base_rate = LOAN_PARAMS["default_rate_good"]
        default_rate = base_rate + (sector_risk / 10) * 0.10

    # Generate repayment history
    repayment_history = []
    defaults = 0
    outstanding = 0

    for i, size in enumerate(loan_sizes):
        if np.random.random() < default_rate:
            status = "defaulted"
            defaults += 1
        elif i >= previous_loans_count - 1 and np.random.random() < 0.3:
            # Recent loan might be outstanding
            status = "active"
            outstanding += int(size * np.random.uniform(0.2, 0.8))
        elif np.random.random() < 0.1:
            status = "restructured"
        else:
            status = "repaid"

        repayment_history.append({
            "loan_amount": int(size),
            "status": status,
        })

    avg_loan_size = int(np.mean(loan_sizes))

    return {
        "previous_loans_count": previous_loans_count,
        "loan_repayment_history": repayment_history,
        "loan_defaults": defaults,
        "outstanding_loans": outstanding,
        "average_loan_size": avg_loan_size,
    }
