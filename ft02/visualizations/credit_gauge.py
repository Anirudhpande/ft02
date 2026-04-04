"""
Credit Score Gauge Chart

Generates a premium semicircular gauge chart showing the credit score
on a 300-900 scale with smooth gradient zones and modern aesthetics.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Wedge
from matplotlib.collections import PatchCollection
import numpy as np
import os


def generate_credit_gauge(business: dict, output_dir: str) -> str:
    """
    Generate a polished credit score gauge chart with modern design.
    Uses a Cartesian (non-polar) approach for pixel-perfect layout control.
    """
    gstin = business["business_identity"]["gstin"]
    score = business.get("credit_score", 500)
    trade_name = business["business_identity"].get("trade_name", "Business")

    score_min, score_max = 300, 900
    score_normalized = (score - score_min) / (score_max - score_min)

    # Risk classification
    if score >= 750:
        risk_text, risk_color = "LOW RISK", "#059669"
    elif score >= 650:
        risk_text, risk_color = "MODERATE RISK", "#D97706"
    elif score >= 500:
        risk_text, risk_color = "HIGH RISK", "#DC2626"
    else:
        risk_text, risk_color = "VERY HIGH RISK", "#991B1B"

    # ── Figure Setup ──
    fig, ax = plt.subplots(figsize=(6, 3.6))
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-0.4, 1.45)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── Draw Gauge Arc (smooth gradient wedges) ──
    n_segments = 200
    outer_r = 1.05
    inner_r = 0.72
    thickness = outer_r - inner_r

    for i in range(n_segments):
        frac = i / n_segments
        angle_start = 180 - (i / n_segments) * 180
        angle_end = 180 - ((i + 1) / n_segments) * 180

        color = plt.cm.RdYlGn(frac)
        wedge = Wedge(
            center=(0, 0), r=outer_r,
            theta1=angle_end, theta2=angle_start,
            width=thickness,
            facecolor=color, edgecolor="none", linewidth=0
        )
        ax.add_patch(wedge)

    # ── Inner shadow ring ──
    inner_ring = Wedge(
        center=(0, 0), r=inner_r,
        theta1=0, theta2=180,
        width=0.03,
        facecolor="#E5E7EB", edgecolor="none"
    )
    ax.add_patch(inner_ring)

    # ── Tick marks at 300, 400, 500, 600, 700, 800, 900 ──
    tick_values = [300, 400, 500, 600, 700, 800, 900]
    for tv in tick_values:
        frac = (tv - score_min) / (score_max - score_min)
        angle = np.radians(180 - frac * 180)
        # Outer tick
        x1 = (outer_r + 0.02) * np.cos(angle)
        y1 = (outer_r + 0.02) * np.sin(angle)
        x2 = (outer_r + 0.08) * np.cos(angle)
        y2 = (outer_r + 0.08) * np.sin(angle)
        ax.plot([x1, x2], [y1, y2], color="#9CA3AF", linewidth=1.2, zorder=5)
        # Label
        lx = (outer_r + 0.18) * np.cos(angle)
        ly = (outer_r + 0.18) * np.sin(angle)
        ax.text(lx, ly, str(tv), ha="center", va="center",
                fontsize=7.5, color="#6B7280", fontweight="600")

    # ── Needle ──
    needle_angle = np.radians(180 - score_normalized * 180)
    needle_len = inner_r - 0.05

    # Needle triangle
    tip_x = needle_len * np.cos(needle_angle)
    tip_y = needle_len * np.sin(needle_angle)
    base_perp = np.array([-np.sin(needle_angle), np.cos(needle_angle)])
    base_w = 0.025
    b1 = base_perp * base_w
    b2 = -base_perp * base_w

    triangle = plt.Polygon(
        [[tip_x, tip_y], [b1[0], b1[1]], [b2[0], b2[1]]],
        facecolor="#1F2937", edgecolor="none", zorder=15
    )
    ax.add_patch(triangle)

    # Center hub
    hub_outer = plt.Circle((0, 0), 0.06, facecolor="#1F2937", edgecolor="#374151", linewidth=1.5, zorder=16)
    hub_inner = plt.Circle((0, 0), 0.025, facecolor="#FFFFFF", edgecolor="none", zorder=17)
    ax.add_patch(hub_outer)
    ax.add_patch(hub_inner)

    # ── Score text (large, centered) ──
    ax.text(0, 0.38, str(score), ha="center", va="center",
            fontsize=44, fontweight="900", color="#111827",
            fontfamily="sans-serif", zorder=20)

    # ── Risk band label ──
    ax.text(0, 0.18, risk_text, ha="center", va="center",
            fontsize=12, fontweight="800", color=risk_color,
            fontfamily="sans-serif", zorder=20)

    # ── Subtitle ──
    ax.text(0, -0.18, trade_name, ha="center", va="center",
            fontsize=9, fontweight="500", color="#9CA3AF",
            fontfamily="sans-serif", zorder=20)

    # ── Colored score badge at bottom ──
    badge_bg = risk_color
    badge = FancyBboxPatch(
        (-0.35, -0.38), 0.7, 0.14,
        boxstyle="round,pad=0.02",
        facecolor=badge_bg, edgecolor="none", alpha=0.12, zorder=18
    )
    ax.add_patch(badge)
    ax.text(0, -0.31, f"Score Range: {score_min} - {score_max}",
            ha="center", va="center", fontsize=7.5,
            color=risk_color, fontweight="600", zorder=20)

    filepath = os.path.join(output_dir, f"gauge_{gstin}.png")
    fig.savefig(filepath, dpi=200, bbox_inches="tight",
                facecolor="#FFFFFF", pad_inches=0.08)
    plt.close(fig)
    return filepath
