"""
Sales Time Series Chart

Generates a line chart of 36-month sales with highlighted anomaly spikes.
"""

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import os


def generate_sales_chart(business: dict, output_dir: str) -> str:
    """
    Generate a sales time-series line chart.

    Args:
        business: Complete business dictionary
        output_dir: Directory to save the chart

    Returns:
        Path to saved chart image
    """
    gstin = business["business_identity"]["gstin"]
    sales_data = business.get("sales_data", {})
    monthly_sales = sales_data.get("monthly_sales", [])
    spikes = sales_data.get("sudden_sales_spikes", [])

    if not monthly_sales:
        return ""

    months = np.arange(1, len(monthly_sales) + 1)
    sales = np.array(monthly_sales)

    fig, ax = plt.subplots(figsize=(12, 5))

    # Main sales line
    ax.plot(months, sales / 100000, color="#2196F3", linewidth=2,
            label="Monthly Sales", zorder=3)

    # Fill under curve
    ax.fill_between(months, 0, sales / 100000, alpha=0.1, color="#2196F3")

    # Highlight spikes
    if spikes:
        spike_months = [m + 1 for m in spikes if m < len(monthly_sales)]
        spike_values = [monthly_sales[m] / 100000 for m in spikes if m < len(monthly_sales)]
        ax.scatter(spike_months, spike_values, color="#F44336", s=100,
                   zorder=5, label="Anomalous Spike", edgecolors="white", linewidth=2)

        # Add annotations for spikes
        for sm, sv in zip(spike_months, spike_values):
            ax.annotate(f"⚠ Month {sm}",
                        xy=(sm, sv), xytext=(sm + 1, sv + sv * 0.1),
                        fontsize=8, color="#F44336", fontweight="bold",
                        arrowprops=dict(arrowstyle="->", color="#F44336", lw=1.5))

    # Trend line
    coeffs = np.polyfit(months, sales / 100000, 1)
    trend = np.polyval(coeffs, months)
    ax.plot(months, trend, "--", color="#FF9800", alpha=0.7, linewidth=1.5,
            label="Trend Line")

    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Sales (Rs. Lakhs)", fontsize=12)
    ax.set_title(f"Monthly Sales — {business['business_identity']['trade_name']}",
                 fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1, len(monthly_sales))
    ax.set_ylim(bottom=0)

    plt.tight_layout()

    filepath = os.path.join(output_dir, f"sales_{gstin}.png")
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return filepath
