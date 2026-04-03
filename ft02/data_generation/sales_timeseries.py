"""
Sales Time Series Generator

Generates 36-month sales data using the time series engine.
Assigns sales patterns based on business archetype and fraud label.
Wraps the timeseries_engine with business-context-aware defaults.
"""

import numpy as np
from utils.constants import (
    SECTORS, REVENUE_GMM_PARAMS, SALES_PATTERN_WEIGHTS,
)
from synthetic_models.gmm_engine import create_revenue_sampler
from synthetic_models.timeseries_engine import generate_sales_timeseries


# Pre-build revenue sampler
_revenue_sampler = create_revenue_sampler(REVENUE_GMM_PARAMS)


def _select_pattern(is_fraud: bool) -> str:
    """Select a sales pattern based on fraud label."""
    patterns = ["seasonal", "steady_growth", "declining", "fraudulent_spike"]

    if is_fraud:
        weights = SALES_PATTERN_WEIGHTS["fraud"]
    else:
        weights = SALES_PATTERN_WEIGHTS["non_fraud"]

    return np.random.choice(patterns, p=weights)


def generate_sales_data(sector: str, business_age: int,
                        is_fraud: bool = False) -> dict:
    """
    Generate 36-month sales time series for a business.

    Args:
        sector: Business sector name
        business_age: Age of business in years
        is_fraud: Whether business is fraudulent

    Returns:
        Dict with monthly_sales, spikes, volatility, and turnover
    """
    # Determine base revenue from sector range + GMM sampling
    sector_info = SECTORS.get(sector, {"typical_turnover_range": (500000, 5000000)})
    turnover_low, turnover_high = sector_info["typical_turnover_range"]

    # Monthly base from annual range
    monthly_low = turnover_low / 12
    monthly_high = turnover_high / 12

    # GMM sample for base, then clip to sector range
    base_revenue = _revenue_sampler.sample_one()
    base_revenue = np.clip(base_revenue, monthly_low, monthly_high)

    # Adjust for business age (older businesses tend to have higher revenue)
    age_factor = 1.0 + min(business_age, 10) * 0.05
    base_revenue *= age_factor

    # Select pattern
    pattern = _select_pattern(is_fraud)

    # Generate time series
    ts_data = generate_sales_timeseries(
        base_revenue=base_revenue,
        pattern=pattern,
        n_months=36,
    )

    return ts_data
