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

    with plt.style.context("dark_background"):
        fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor('#121212')
        ax.set_facecolor('#121212')

        # Glow lines for radar
        for w, alpha in [(8, 0.1), (5, 0.25), (3, 0.4)]:
            ax.plot(angles, values, "-", linewidth=w, color="#1E88E5", alpha=alpha, zorder=2)

        # Draw the main radar
        ax.plot(angles, values, "o-", linewidth=2.5, color="#64B5F6", markersize=8, label="Current Business", zorder=3)
        ax.fill(angles, values, alpha=0.2, color="#2196F3", zorder=1)

        # Draw reference circles
        for level in [0.25, 0.50, 0.75, 1.0]:
            ref_values = [level] * (N + 1)
            ax.plot(angles, ref_values, "--", linewidth=1, color="#555555", alpha=0.5, zorder=0)

        # Color zones on each axis
        for i, (cat, val) in enumerate(zip(categories, values[:-1])):
            if val >= 0.7:
                color = "#4CAF50"
            elif val >= 0.4:
                color = "#FF9800"
            else:
                color = "#F44336"

            ax.plot([angles[i]], [val], "o", color=color, markersize=14, zorder=4, alpha=0.4)
            ax.plot([angles[i]], [val], "o", color=color, markersize=8, zorder=5, markeredgewidth=1.5, markeredgecolor="#ffffff")

        # Labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=11, fontweight="bold", color="#cccccc")

        # Y-axis labels
        ax.set_yticks([0.25, 0.50, 0.75, 1.0])
        ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=9, color="#777777")
        ax.set_ylim(0, 1.1)

        ax.spines['polar'].set_color('#333333')

        ax.set_title(
            f"Risk Assessment Radar — {business['business_identity']['trade_name']}",
            pad=35, fontsize=18, fontweight="bold", color="#ffffff"
        )

        # Legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker="o", color="#121212", markerfacecolor="#4CAF50", markersize=10, label="Strong (≥70%)"),
            Line2D([0], [0], marker="o", color="#121212", markerfacecolor="#FF9800", markersize=10, label="Moderate (40-70%)"),
            Line2D([0], [0], marker="o", color="#121212", markerfacecolor="#F44336", markersize=10, label="Weak (<40%)"),
        ]
        ax.legend(handles=legend_elements, loc="upper right", bbox_to_anchor=(1.25, 1.15), 
                  fontsize=10, facecolor="#000000", edgecolor="#333333")

        plt.tight_layout()

        filepath = os.path.join(output_dir, f"radar_{gstin}.png")
        fig.savefig(filepath, dpi=300, bbox_inches="tight", facecolor='#121212', transparent=False)
        plt.close(fig)

    return filepath
