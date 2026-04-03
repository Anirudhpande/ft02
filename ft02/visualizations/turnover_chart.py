"""
Turnover Analysis Chart

Generates turnover analysis with monthly revenue bars, growth trend,
and key metrics: annual turnover, monthly average, growth rate,
volatility index.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os


def calculate_turnover_metrics(business: dict) -> dict:
    """
    Calculate turnover analysis metrics.

    Args:
        business: Complete business dictionary

    Returns:
        Dict with annual turnover, monthly average, growth rate, volatility
    """
    sales_data = business.get("sales_data", {})
    monthly_sales = sales_data.get("monthly_sales", [])

    if not monthly_sales:
        return {
            "estimated_annual_turnover": 0,
            "monthly_average_revenue": 0,
            "growth_rate": 0,
            "volatility_index": 0,
        }

    sales = np.array(monthly_sales)
    n = len(sales)

    # Annual turnover (extrapolate from available months)
    annual_factor = 12.0 / min(n, 12)
    last_12 = sales[-12:] if n >= 12 else sales
    estimated_annual = float(np.sum(last_12) * annual_factor)

    # Monthly average
    monthly_avg = float(np.mean(sales))

    # Growth rate (annualized)
    if n > 1:
        t = np.arange(n)
        coeffs = np.polyfit(t, sales, 1)
        monthly_growth = coeffs[0] / max(np.mean(sales), 1)
        annual_growth = monthly_growth * 12
    else:
        annual_growth = 0.0

    # Volatility index (CV)
    volatility = float(np.std(sales) / max(np.mean(sales), 1))

    return {
        "estimated_annual_turnover": round(estimated_annual, 2),
        "monthly_average_revenue": round(monthly_avg, 2),
        "growth_rate": round(float(annual_growth), 4),
        "volatility_index": round(volatility, 4),
    }


def generate_turnover_chart(business: dict, output_dir: str) -> str:
    """
    Generate a turnover analysis chart.

    Args:
        business: Complete business dictionary
        output_dir: Directory to save the chart

    Returns:
        Path to saved chart image
    """
    gstin = business["business_identity"]["gstin"]
    sales_data = business.get("sales_data", {})
    monthly_sales = sales_data.get("monthly_sales", [])
    metrics = calculate_turnover_metrics(business)

    if not monthly_sales:
        return ""

    months = np.arange(1, len(monthly_sales) + 1)
    sales = np.array(monthly_sales)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5),
                                     gridspec_kw={"width_ratios": [2, 1]})

    # ── Left: Monthly revenue bars + trend ──────────────────────────────────
    colors = []
    for i, s in enumerate(sales):
        if i > 0 and sales[i - 1] > 0:
            change = (s - sales[i - 1]) / sales[i - 1]
            if change > 0.5:
                colors.append("#F44336")  # Spike
            elif change < -0.3:
                colors.append("#FF9800")  # Drop
            else:
                colors.append("#2196F3")  # Normal
        else:
            colors.append("#2196F3")

    ax1.bar(months, sales / 100000, color=colors, alpha=0.8, width=0.8)

    # Trend line
    coeffs = np.polyfit(months, sales / 100000, 1)
    trend = np.polyval(coeffs, months)
    ax1.plot(months, trend, "--", color="#333", linewidth=2, label="Trend")

    # Moving average (3-month)
    if len(sales) >= 3:
        ma = np.convolve(sales / 100000, np.ones(3) / 3, mode="valid")
        ax1.plot(np.arange(2, len(ma) + 2), ma, color="#9C27B0",
                 linewidth=2, alpha=0.7, label="3-Month MA")

    ax1.set_xlabel("Month", fontsize=11)
    ax1.set_ylabel("Revenue (Rs. Lakhs)", fontsize=11)
    ax1.set_title("Monthly Revenue", fontsize=13, fontweight="bold")
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    # ── Right: Key metrics table ────────────────────────────────────────────
    ax2.axis("off")

    metric_labels = [
        ("Annual Turnover", f"Rs.{metrics['estimated_annual_turnover'] / 100000:.1f}L"),
        ("Monthly Average", f"Rs.{metrics['monthly_average_revenue'] / 100000:.1f}L"),
        ("Growth Rate", f"{metrics['growth_rate']:.1%}"),
        ("Volatility Index", f"{metrics['volatility_index']:.2f}"),
    ]

    y_start = 0.85
    for i, (label, value) in enumerate(metric_labels):
        y = y_start - i * 0.20

        # Label
        ax2.text(0.1, y, label, fontsize=12, fontweight="bold",
                 transform=ax2.transAxes, va="center")
        # Value
        color = "#4CAF50"
        if "Growth" in label and metrics["growth_rate"] < 0:
            color = "#F44336"
        if "Volatility" in label and metrics["volatility_index"] > 0.4:
            color = "#FF9800"

        ax2.text(0.1, y - 0.07, value, fontsize=16, fontweight="bold",
                 color=color, transform=ax2.transAxes, va="center")

    ax2.set_title("Key Metrics", fontsize=13, fontweight="bold")

    fig.suptitle(
        f"Turnover Analysis — {business['business_identity']['trade_name']}",
        fontsize=14, fontweight="bold", y=1.02
    )

    plt.tight_layout()

    filepath = os.path.join(output_dir, f"turnover_{gstin}.png")
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return filepath
