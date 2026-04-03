"""
Risk Radar Chart

Generates a radar/spider chart showing 6 business risk dimensions:
GST compliance, financial stability, vendor diversification,
repayment reliability, sales stability, sector risk.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os


def generate_risk_radar(business: dict, output_dir: str) -> str:
    """
    Generate a risk radar chart for a business.

    Args:
        business: Complete business dictionary
        output_dir: Directory to save the chart

    Returns:
        Path to saved chart image
    """
    gstin = business["business_identity"]["gstin"]
    features = business.get("_credit_features", {})

    if not features:
        return ""

    # ── Define 6 risk dimensions (all normalized to 0-1, higher = better) ──
    dimensions = {
        "GST\nCompliance":       features.get("gst_compliance_score", 0.5),
        "Financial\nStability":  features.get("turnover_stability", 0.5),
        "Vendor\nDiversification": features.get("vendor_diversification", 0.5),
        "Repayment\nReliability": features.get("repayment_ratio", 0.5),
        "Sales\nStability":      1.0 - min(features.get("sales_volatility", 0.5), 1.0),
        "Sector\nSafety":        1.0 - features.get("sector_risk", 0.5),
    }

    categories = list(dimensions.keys())
    values = list(dimensions.values())

    # Close the radar
    values += values[:1]
    N = len(categories)

    # Angles for each axis
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    # Draw the radar
    ax.plot(angles, values, "o-", linewidth=2.5, color="#2196F3",
            markersize=8, label="Current Business")
    ax.fill(angles, values, alpha=0.15, color="#2196F3")

    # Draw reference circles
    for level in [0.25, 0.50, 0.75, 1.0]:
        ref_values = [level] * (N + 1)
        ax.plot(angles, ref_values, "--", linewidth=0.5, color="#CCCCCC", alpha=0.7)

    # Color zones on each axis
    for i, (cat, val) in enumerate(zip(categories, values[:-1])):
        if val >= 0.7:
            color = "#4CAF50"
        elif val >= 0.4:
            color = "#FF9800"
        else:
            color = "#F44336"

        ax.plot([angles[i]], [val], "o", color=color, markersize=10, zorder=5)

    # Labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10, fontweight="bold")

    # Y-axis labels
    ax.set_yticks([0.25, 0.50, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=8, color="#999")
    ax.set_ylim(0, 1.05)

    ax.set_title(
        f"Risk Assessment Radar — {business['business_identity']['trade_name']}",
        pad=25, fontsize=14, fontweight="bold"
    )

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#4CAF50",
               markersize=10, label="Strong (≥70%)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#FF9800",
               markersize=10, label="Moderate (40-70%)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#F44336",
               markersize=10, label="Weak (<40%)"),
    ]
    ax.legend(handles=legend_elements, loc="upper right",
              bbox_to_anchor=(1.3, 1.1), fontsize=9)

    plt.tight_layout()

    filepath = os.path.join(output_dir, f"radar_{gstin}.png")
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return filepath
