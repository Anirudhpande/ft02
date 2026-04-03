"""
Credit Score Gauge Chart

Generates a semicircular gauge chart showing the credit score
on a 300-900 scale with color zones.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os


def generate_credit_gauge(business: dict, output_dir: str) -> str:
    """
    Generate a credit score gauge chart.

    Args:
        business: Complete business dictionary
        output_dir: Directory to save the chart

    Returns:
        Path to saved chart image
    """
    gstin = business["business_identity"]["gstin"]
    score = business.get("credit_score", 500)

    fig, ax = plt.subplots(figsize=(8, 5), subplot_kw={"projection": "polar"})

    # Gauge parameters
    score_min, score_max = 300, 900
    score_range = score_max - score_min

    # Normalize score to angle (π to 0, left to right)
    score_normalized = (score - score_min) / score_range
    needle_angle = np.pi * (1 - score_normalized)

    # Draw color zones (from left/bad to right/good)
    n_segments = 100
    angles = np.linspace(np.pi, 0, n_segments)

    for i in range(n_segments - 1):
        frac = i / n_segments
        if frac < 0.33:
            color = plt.cm.RdYlGn(frac / 0.33 * 0.3)
        elif frac < 0.67:
            color = plt.cm.RdYlGn(0.3 + (frac - 0.33) / 0.34 * 0.4)
        else:
            color = plt.cm.RdYlGn(0.7 + (frac - 0.67) / 0.33 * 0.3)

        ax.barh(0.8, angles[i] - angles[i + 1],
                left=angles[i + 1], height=0.3,
                color=color, edgecolor="none")

    # Draw needle
    ax.plot([needle_angle, needle_angle], [0, 0.95],
            color="#333333", linewidth=3, zorder=10)
    ax.scatter([needle_angle], [0], color="#333333", s=80, zorder=11)

    # Score text
    ax.text(np.pi / 2, 0.35, str(score),
            ha="center", va="center", fontsize=36,
            fontweight="bold", color="#333333")

    # Risk band
    if score >= 750:
        risk_text = "LOW RISK"
        risk_color = "#4CAF50"
    elif score >= 650:
        risk_text = "MEDIUM RISK"
        risk_color = "#FF9800"
    elif score >= 500:
        risk_text = "HIGH RISK"
        risk_color = "#FF5722"
    else:
        risk_text = "VERY HIGH RISK"
        risk_color = "#F44336"

    ax.text(np.pi / 2, 0.05, risk_text,
            ha="center", va="center", fontsize=14,
            fontweight="bold", color=risk_color)

    # Labels at edges
    ax.text(np.pi, 1.25, "300", ha="center", va="center",
            fontsize=10, color="#999")
    ax.text(0, 1.25, "900", ha="center", va="center",
            fontsize=10, color="#999")
    ax.text(np.pi / 2, 1.25, "600", ha="center", va="center",
            fontsize=10, color="#999")

    # Hide lower half and axes
    ax.set_ylim(0, 1.4)
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines["polar"].set_visible(False)

    ax.set_title(f"Credit Score — {business['business_identity']['trade_name']}",
                 pad=20, fontsize=14, fontweight="bold")

    filepath = os.path.join(output_dir, f"gauge_{gstin}.png")
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return filepath
