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

    # Modern Dark Theme
    bg_color = "#111827"
    text_color = "#F3F4F6"
    
    fig, ax = plt.subplots(figsize=(7, 3.5), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    score_min, score_max = 300, 900
    score_range = score_max - score_min

    # Normalize score
    score_normalized = (score - score_min) / score_range
    needle_angle = np.pi * (1 - score_normalized)

    # Gradient Zones
    n_segments = 150
    angles = np.linspace(np.pi, 0, n_segments)

    for i in range(n_segments - 1):
        frac = i / n_segments
        # Interpolate across Red -> Orange -> Yellowgreen -> Green
        color = plt.cm.RdYlGn(frac)
        ax.barh(1.0, angles[i] - angles[i + 1],
                left=angles[i + 1], height=0.4,
                color=color, edgecolor="none", zorder=1)

    # Sleek Needle
    ax.plot([needle_angle, needle_angle], [0, 1.1],
            color="#FFFFFF", linewidth=4, zorder=10, solid_capstyle='round')
    ax.scatter([needle_angle], [0], color="#FFFFFF", s=150, zorder=11)
    ax.scatter([needle_angle], [0], color=bg_color, s=50, zorder=12)

    # Score numeric display
    ax.text(np.pi / 2, 0.2, str(score),
            ha="center", va="center", fontsize=48,
            fontweight="bold", color=text_color, fontfamily='sans-serif')

    # Risk band mapping
    if score >= 750:
        risk_text, risk_color = "LOW RISK", "#10B981"
    elif score >= 650:
        risk_text, risk_color = "MEDIUM RISK", "#F59E0B"
    elif score >= 500:
        risk_text, risk_color = "HIGH RISK", "#EF4444"
    else:
        risk_text, risk_color = "VERY HIGH RISK", "#DC2626"

    ax.text(np.pi / 2, 0.6, risk_text,
            ha="center", va="center", fontsize=14,
            fontweight="900", color=risk_color, fontfamily='sans-serif')

    # Minimal edge labels
    ax.text(np.pi, 1.45, "300", ha="center", va="center", fontsize=12, color="#6B7280", fontweight="bold")
    ax.text(0, 1.45, "900", ha="center", va="center", fontsize=12, color="#6B7280", fontweight="bold")

    # Clean axes
    ax.set_ylim(0, 1.5)
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines["polar"].set_visible(False)
    ax.grid(False)

    filepath = os.path.join(output_dir, f"gauge_{gstin}.png")
    fig.savefig(filepath, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor(), pad_inches=0.1)
    plt.close(fig)

    return filepath
