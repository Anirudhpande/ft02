"""
Time Series Simulation Engine

Generates realistic monthly sales time series using:
- AR(1) autoregressive process
- Seasonal sinusoidal components
- Linear trend (positive or negative)
- Optional fraud spike injection

Model: y_t = α + β*t + γ*sin(2π*t/12) + φ*y_{t-1} + ε_t
"""

import numpy as np
from utils.constants import TIMESERIES_PARAMS


def generate_sales_timeseries(base_revenue: float, pattern: str,
                              n_months: int = 36,
                              seed: int = None) -> dict:
    """
    Generate a monthly sales time series for a business.

    Args:
        base_revenue: Base monthly revenue level
        pattern: One of 'seasonal', 'steady_growth', 'declining', 'fraudulent_spike'
        n_months: Number of months to simulate (default 36)
        seed: Optional random seed for reproducibility

    Returns:
        Dict with:
            - monthly_sales: list of monthly values
            - sudden_sales_spikes: list of spike month indices
            - sales_volatility: coefficient of variation
            - estimated_turnover: total over the period
    """
    if seed is not None:
        rng = np.random.RandomState(seed)
    else:
        rng = np.random.RandomState()

    params = TIMESERIES_PARAMS[pattern]

    trend = params["trend"]
    seasonal_amp = params["seasonal_amplitude"]
    noise_std = params["noise_std"]
    ar_coeff = params["ar_coeff"]

    # Generate time series
    sales = np.zeros(n_months)
    sales[0] = base_revenue * (1 + rng.normal(0, noise_std))

    for t in range(1, n_months):
        # Trend component
        trend_component = base_revenue * trend * t

        # Seasonal component (12-month cycle)
        seasonal_component = base_revenue * seasonal_amp * np.sin(2 * np.pi * t / 12)

        # AR(1) component
        ar_component = ar_coeff * (sales[t - 1] - base_revenue)

        # Noise
        noise = base_revenue * noise_std * rng.normal()

        # Combine
        sales[t] = base_revenue + trend_component + seasonal_component + ar_component + noise

    # Ensure no negative values
    sales = np.maximum(sales, base_revenue * 0.05)

    # ── Inject fraud spikes if pattern is fraudulent ────────────────────────
    spike_months = []

    if pattern == "fraudulent_spike":
        spike_params = params
        multiplier = rng.uniform(*spike_params["spike_multiplier_range"])
        spike_start = rng.randint(*spike_params["spike_month_range"])
        spike_duration = rng.randint(*spike_params["spike_duration"])

        spike_start = min(spike_start, n_months - spike_duration)

        for m in range(spike_start, min(spike_start + spike_duration, n_months)):
            sales[m] *= multiplier
            spike_months.append(int(m))

    # ── Detect natural spikes (>100% month-over-month increase) ─────────────
    for t in range(1, n_months):
        if sales[t] > sales[t - 1] * 2.0:
            if t not in spike_months:
                spike_months.append(int(t))

    # ── Calculate derived metrics ───────────────────────────────────────────
    sales_list = [round(float(s), 2) for s in sales]
    mean_sales = np.mean(sales)
    std_sales = np.std(sales)
    volatility = float(std_sales / mean_sales) if mean_sales > 0 else 0.0
    total_turnover = float(np.sum(sales))

    return {
        "monthly_sales": sales_list,
        "sudden_sales_spikes": sorted(spike_months),
        "sales_volatility": round(volatility, 4),
        "estimated_turnover": round(total_turnover, 2),
    }


def classify_growth_pattern(monthly_sales: list) -> str:
    """
    Classify the growth pattern of a sales time series.

    Returns one of: 'growing', 'stable', 'declining', 'volatile'
    """
    if len(monthly_sales) < 6:
        return "stable"

    sales = np.array(monthly_sales)

    # Linear regression for trend
    t = np.arange(len(sales))
    coeffs = np.polyfit(t, sales, 1)
    slope = coeffs[0]
    mean_val = np.mean(sales)

    # Normalized slope (% change per month)
    norm_slope = slope / mean_val if mean_val > 0 else 0

    # Volatility
    cv = np.std(sales) / mean_val if mean_val > 0 else 0

    if cv > 0.5:
        return "volatile"
    elif norm_slope > 0.02:
        return "growing"
    elif norm_slope < -0.02:
        return "declining"
    else:
        return "stable"
