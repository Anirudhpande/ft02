"""
Credit Score Gauge Chart

Generates a premium semicircular gauge chart showing the credit score
on a 300-900 scale with smooth gradient zones and modern aesthetics.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os


def generate_credit_gauge(business: dict, output_dir: str) -> str:
    gstin = business["business_identity"]["gstin"]
    score = business.get("credit_score", 500)
    trade_name = business["business_identity"].get("trade_name", "Business")

    # Use a dark modern aesthetic
    with plt.style.context("dark_background"):
        fig, ax = plt.subplots(figsize=(10, 6), subplot_kw={"projection": "polar"})
        fig.patch.set_facecolor('#121212')
        ax.set_facecolor('#121212')

        score_min, score_max = 300, 900
        score_range = score_max - score_min
        score_normalized = (score - score_min) / score_range
        needle_angle = np.pi * (1 - score_normalized)

        # Smooth elegant gradients
        n_segments = 200
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
                    left=angles[i + 1], height=0.25,
                    color=color, edgecolor="none", alpha=0.85)

        # Draw glowing needle
        # Glow layers
        for glow_w, glow_alpha in zip([9, 7, 5], [0.1, 0.3, 0.5]):
            ax.plot([needle_angle, needle_angle], [0, 0.95],
                    color="#ffffff", linewidth=glow_w, alpha=glow_alpha, zorder=8)
        
        # Solid core needle
        ax.plot([needle_angle, needle_angle], [0, 0.95],
                color="#ffffff", linewidth=3, zorder=10)
        ax.scatter([needle_angle], [0], color="#ffffff", s=120, zorder=11)
        ax.scatter([needle_angle], [0], color="#2196F3", s=40, zorder=12)

        # Drop shadow text for Score
        ax.text(np.pi / 2, 0.34, str(score),
                ha="center", va="center", fontsize=48,
                fontweight="black", color="#000000", alpha=0.3)
        ax.text(np.pi / 2, 0.35, str(score),
                ha="center", va="center", fontsize=48,
                fontweight="black", color="#ffffff")

        if score >= 750:
            risk_text, risk_color = "LOW RISK", "#4CAF50"
        elif score >= 650:
            risk_text, risk_color = "MEDIUM RISK", "#FF9800"
        elif score >= 500:
            risk_text, risk_color = "HIGH RISK", "#FF5722"
        else:
            risk_text, risk_color = "VERY HIGH RISK", "#F44336"

        ax.text(np.pi / 2, 0.05, risk_text,
                ha="center", va="center", fontsize=16,
                fontweight="bold", color=risk_color)

        ax.text(np.pi, 1.25, "300", ha="center", va="center", fontsize=11, color="#777")
        ax.text(0, 1.25, "900", ha="center", va="center", fontsize=11, color="#777")
        ax.text(np.pi / 2, 1.25, "600", ha="center", va="center", fontsize=11, color="#777")

        ax.set_ylim(0, 1.4)
        ax.set_thetamin(0)
        ax.set_thetamax(180)
        ax.set_yticks([])
        ax.set_xticks([])
        ax.spines["polar"].set_visible(False)

        ax.set_title(f"Credit Rating — {business['business_identity']['trade_name']}",
                     pad=25, fontsize=18, fontweight="bold", color="#ffffff")

        plt.tight_layout()

        filepath = os.path.join(output_dir, f"gauge_{gstin}.png")
        fig.savefig(filepath, dpi=300, bbox_inches="tight", facecolor='#121212', transparent=False)
        plt.close(fig)

    return filepath
