"""
Sales Time Series Chart

Generates a line chart of 36-month sales with highlighted anomaly spikes.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os


def generate_sales_chart(business: dict, output_dir: str) -> str:
    gstin = business["business_identity"]["gstin"]
    sales_data = business.get("sales_data", {})
    monthly_sales = sales_data.get("monthly_sales", [])
    spikes = sales_data.get("sudden_sales_spikes", [])

    if not monthly_sales:
        return ""

    months = np.arange(1, len(monthly_sales) + 1)
    sales = np.array(monthly_sales)

    with plt.style.context("dark_background"):
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#121212')
        ax.set_facecolor('#121212')

        # Glow layers for main line
        for glow_w, glow_alpha in zip([7, 5, 3], [0.1, 0.25, 0.4]):
            ax.plot(months, sales / 100000, color="#2196F3", linewidth=glow_w, alpha=glow_alpha, zorder=2)

        # Main sales line
        ax.plot(months, sales / 100000, color="#64B5F6", linewidth=2.5, label="Monthly Sales", zorder=3)

        # Fill under curve
        ax.fill_between(months, 0, sales / 100000, alpha=0.15, color="#2196F3")

        # Highlight spikes
        if spikes:
            spike_months = [m + 1 for m in spikes if m < len(monthly_sales)]
            spike_values = [monthly_sales[m] / 100000 for m in spikes if m < len(monthly_sales)]
            
            # Glow for anomalies
            ax.scatter(spike_months, spike_values, color="#F44336", s=250, zorder=4, alpha=0.3)
            ax.scatter(spike_months, spike_values, color="#F44336", s=100, zorder=5, edgecolors="#ffffff", linewidth=1.5)

            # Annotations
            for sm, sv in zip(spike_months, spike_values):
                ax.annotate(f"⚠ Month {sm}",
                            xy=(sm, sv), xytext=(sm + 0.8, sv + sv * 0.1),
                            fontsize=10, color="#FF5252", fontweight="bold",
                            arrowprops=dict(arrowstyle="->", color="#FF5252", lw=1.5))

        # Trend line
        coeffs = np.polyfit(months, sales / 100000, 1)
        trend = np.polyval(coeffs, months)
        ax.plot(months, trend, "--", color="#FFB74D", alpha=0.8, linewidth=1.5, label="Trend Line")

        ax.set_xlabel("Month", fontsize=12, color="#cccccc")
        ax.set_ylabel("Sales (Rs. Lakhs)", fontsize=12, color="#cccccc")
        ax.set_title(f"Monthly Sales Trend — {business['business_identity']['trade_name']}",
                     fontsize=16, fontweight="bold", color="#ffffff", pad=15)
        
        ax.legend(loc="upper left", framealpha=0.2, facecolor="#000000", edgecolor="#333333", fontsize=10)
        ax.grid(True, alpha=0.15, color="#cccccc", linestyle="--")
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#333333')
        ax.spines['left'].set_color('#333333')

        ax.set_xlim(1, len(monthly_sales))
        ax.set_ylim(bottom=0)

        plt.tight_layout()

        filepath = os.path.join(output_dir, f"sales_{gstin}.png")
        fig.savefig(filepath, dpi=300, bbox_inches="tight", facecolor='#121212', transparent=False)
        plt.close(fig)

    return filepath
