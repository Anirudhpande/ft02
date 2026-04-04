"""
Fraud Ring Topology Chart

Generates a dedicated visualization specifically for circular fund rotation
patterns (closed-loop money rotation) detected among MSMEs.
Produces both a static matplotlib PNG and an interactive PyVis HTML graph.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
import networkx as nx
import numpy as np
import os


def generate_fraud_ring_chart(business: dict, output_dir: str) -> str:
    """
    Generate a focused fraud ring topology chart that only shows
    the circular trading patterns (closed-loop money rotation).
    """
    gstin = business["business_identity"]["gstin"]
    network = business.get("network_data", {})
    circular = network.get("circular_trades", [])
    edges = network.get("edges", [])

    if not circular:
        # Generate a "no fraud rings detected" placeholder
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor("#0f172a")
        ax.set_facecolor("#0f172a")
        ax.text(0.5, 0.55, "NO FRAUD RINGS DETECTED", ha="center", va="center",
                fontsize=22, fontweight="900", color="#10B981", fontfamily="sans-serif",
                transform=ax.transAxes)
        ax.text(0.5, 0.4, "No circular fund rotation patterns found in the transaction network",
                ha="center", va="center", fontsize=11, color="#6B7280",
                fontfamily="sans-serif", transform=ax.transAxes)
        ax.text(0.5, 0.3, f"GSTIN: {gstin}", ha="center", va="center",
                fontsize=9, color="#4B5563", fontfamily="sans-serif", transform=ax.transAxes)
        ax.axis("off")
        filepath = os.path.join(output_dir, f"fraud_ring_{gstin}.png")
        fig.savefig(filepath, dpi=200, bbox_inches="tight", facecolor="#0f172a", pad_inches=0.2)
        plt.close(fig)
        return filepath

    # Build a graph containing ONLY the fraud ring entities and edges
    G = nx.DiGraph()

    cycle_nodes = set()
    cycle_edges_list = []
    for cycle in circular:
        path = cycle.get("path", [])
        funds = cycle.get("rotated_funds", 0)
        for node in path:
            cycle_nodes.add(node)
        for i in range(len(path) - 1):
            cycle_edges_list.append((path[i], path[i + 1], funds))

    for node in cycle_nodes:
        G.add_node(node)

    for src, tgt, funds in cycle_edges_list:
        if G.has_edge(src, tgt):
            G[src][tgt]["weight"] += funds
            G[src][tgt]["count"] += 1
        else:
            G.add_edge(src, tgt, weight=funds, count=1)

    # ── Figure Setup ──
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#0f172a")

    # Layout — circular looks best for fraud rings
    if len(G.nodes()) <= 6:
        pos = nx.circular_layout(G, scale=1.5)
    else:
        pos = nx.spring_layout(G, k=2.5, iterations=80, seed=42)

    # ── Draw edges with gradient-like styling ──
    for u, v, data in G.edges(data=True):
        amt = data.get("weight", 0)
        count = data.get("count", 1)
        width = min(5, 1.5 + count * 0.8)
        alpha = min(1.0, 0.5 + count * 0.15)

        # Draw edge
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle="-|>",
                color="#EF4444",
                lw=width,
                alpha=alpha,
                mutation_scale=20,
                connectionstyle="arc3,rad=0.15"
            ),
            zorder=2
        )

        # Edge label (amount)
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        # Offset label perpendicular to edge
        dx, dy = x2 - x1, y2 - y1
        length = max(0.01, np.sqrt(dx**2 + dy**2))
        offset_x = -dy / length * 0.12
        offset_y = dx / length * 0.12
        if amt > 0:
            ax.text(mid_x + offset_x, mid_y + offset_y,
                    f"Rs.{int(amt):,}", ha="center", va="center",
                    fontsize=7.5, color="#FCA5A5", fontweight="600",
                    fontfamily="sans-serif",
                    bbox=dict(boxstyle="round,pad=0.15", facecolor="#1E293B",
                              edgecolor="#EF4444", alpha=0.85, linewidth=0.5),
                    zorder=5)

    # ── Draw nodes ──
    for node in G.nodes():
        x, y = pos[node]
        is_target = (node == gstin)

        if is_target:
            # Target node — large blue circle with glow
            glow = plt.Circle((x, y), 0.22, facecolor="#3B82F6", alpha=0.15, edgecolor="none", zorder=3)
            ax.add_patch(glow)
            circle = plt.Circle((x, y), 0.15, facecolor="#1E3A8A", edgecolor="#3B82F6",
                                linewidth=3, zorder=6)
            ax.add_patch(circle)
            ax.text(x, y + 0.01, "TARGET", ha="center", va="center",
                    fontsize=8, fontweight="900", color="#FFFFFF", fontfamily="sans-serif", zorder=7)
            ax.text(x, y - 0.25, node[:10], ha="center", va="center",
                    fontsize=6.5, color="#93C5FD", fontfamily="sans-serif", zorder=7)
        else:
            # Fraud ring entity — red node
            glow = plt.Circle((x, y), 0.18, facecolor="#EF4444", alpha=0.1, edgecolor="none", zorder=3)
            ax.add_patch(glow)
            circle = plt.Circle((x, y), 0.12, facecolor="#7F1D1D", edgecolor="#EF4444",
                                linewidth=2.5, zorder=6)
            ax.add_patch(circle)
            # Abbreviate long GSTINs
            label = node[:6] if len(node) > 8 else node
            ax.text(x, y, label, ha="center", va="center",
                    fontsize=7, fontweight="700", color="#FCA5A5", fontfamily="sans-serif", zorder=7)

    # ── Title & Stats ──
    total_rotated = sum(ct.get("rotated_funds", 0) for ct in circular)
    ax.text(0.02, 0.98, "FRAUD RING TOPOLOGY", ha="left", va="top",
            fontsize=16, fontweight="900", color="#F1F5F9", fontfamily="sans-serif",
            transform=ax.transAxes, zorder=10)
    ax.text(0.02, 0.93, f"{len(circular)} Circular Pattern(s) Detected  |  "
                        f"{len(cycle_nodes)} Entities Involved  |  "
                        f"Rs.{int(total_rotated):,} Rotated",
            ha="left", va="top", fontsize=9, color="#94A3B8", fontfamily="sans-serif",
            transform=ax.transAxes, zorder=10)

    # ── Legend ──
    legend_y = 0.85
    legend_items = [
        ("#3B82F6", "Target Business"),
        ("#EF4444", "Fraud Ring Entity"),
    ]
    for color, label in legend_items:
        ax.plot(0.02, legend_y, 'o', markersize=8, color=color, transform=ax.transAxes, zorder=10)
        ax.text(0.05, legend_y, label, ha="left", va="center",
                fontsize=8, color="#CBD5E1", fontfamily="sans-serif",
                transform=ax.transAxes, zorder=10)
        legend_y -= 0.045

    # Arrow legend
    ax.annotate("", xy=(0.07, legend_y + 0.005), xytext=(0.02, legend_y + 0.005),
                arrowprops=dict(arrowstyle="-|>", color="#EF4444", lw=2),
                xycoords="axes fraction", textcoords="axes fraction", zorder=10)
    ax.text(0.09, legend_y + 0.005, "Fund Rotation Flow",
            ha="left", va="center", fontsize=8, color="#CBD5E1",
            fontfamily="sans-serif", transform=ax.transAxes, zorder=10)

    # ── Alert banner at bottom ──
    if circular:
        ax.text(0.5, 0.02,
                f"⚠ ALERT: {len(circular)} closed-loop fund rotation pattern(s) detected — "
                f"potential artificial transaction velocity inflation",
                ha="center", va="bottom", fontsize=9, fontweight="700",
                color="#FCA5A5", fontfamily="sans-serif",
                transform=ax.transAxes,
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#450A0A",
                          edgecolor="#DC2626", alpha=0.9, linewidth=1),
                zorder=10)

    ax.axis("off")
    # Auto-scale
    margin = 0.5
    all_x = [pos[n][0] for n in G.nodes()]
    all_y = [pos[n][1] for n in G.nodes()]
    ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
    ax.set_ylim(min(all_y) - margin, max(all_y) + margin)

    filepath = os.path.join(output_dir, f"fraud_ring_{gstin}.png")
    fig.savefig(filepath, dpi=200, bbox_inches="tight", facecolor="#0f172a", pad_inches=0.15)
    plt.close(fig)
    return filepath


def generate_fraud_ring_html(business: dict, output_dir: str) -> str:
    """
    Generate an interactive PyVis HTML visualization specifically for fraud rings.
    Dark theme, highlighting closed-loop money rotation patterns.
    """
    from pyvis.network import Network

    gstin = business["business_identity"]["gstin"]
    network = business.get("network_data", {})
    circular = network.get("circular_trades", [])

    if not circular:
        return ""

    net = Network(
        height="550px", width="100%", directed=True,
        bgcolor="#0f172a", font_color="white"
    )

    cycle_nodes = set()
    cycle_edges = set()
    edge_funds = {}

    for cycle in circular:
        path = cycle.get("path", [])
        funds = cycle.get("rotated_funds", 0)
        cycle_nodes.update(path)
        for i in range(len(path) - 1):
            edge_key = (path[i], path[i + 1])
            cycle_edges.add(edge_key)
            edge_funds[edge_key] = edge_funds.get(edge_key, 0) + funds

    # Add nodes
    for node in cycle_nodes:
        if node == gstin:
            net.add_node(
                node, label="TARGET",
                color={"background": "#1E3A8A", "border": "#3B82F6",
                       "highlight": {"background": "#2563EB", "border": "#60A5FA"}},
                size=35, font={"size": 14, "color": "white", "bold": True},
                title=f"<b>TARGET BUSINESS</b><br>GSTIN: {node}",
                borderWidth=3, borderWidthSelected=5,
                shadow={"enabled": True, "color": "rgba(59,130,246,0.4)", "size": 15}
            )
        else:
            label = node[:6] if len(node) > 8 else node
            net.add_node(
                node, label=label,
                color={"background": "#7F1D1D", "border": "#EF4444",
                       "highlight": {"background": "#991B1B", "border": "#F87171"}},
                size=25, font={"size": 11, "color": "#FCA5A5"},
                title=f"<b>FRAUD RING ENTITY</b><br>GSTIN: {node}",
                borderWidth=2.5, borderWidthSelected=4,
                shadow={"enabled": True, "color": "rgba(239,68,68,0.3)", "size": 10}
            )

    # Add edges
    for (u, v) in cycle_edges:
        funds = edge_funds.get((u, v), 0)
        funds_str = f"Rs.{int(funds):,}" if funds else "Unknown"
        net.add_edge(
            u, v,
            title=f"<b>Rotated Funds:</b> {funds_str}",
            color={"color": "#EF4444", "highlight": "#F87171", "opacity": 0.85},
            width=3.5,
            label=funds_str if funds else "",
            font={"size": 10, "color": "#FCA5A5", "strokeWidth": 0},
            smooth={"type": "curvedCW", "roundness": 0.2},
            arrows={"to": {"enabled": True, "scaleFactor": 1.2}}
        )

    net.set_options("""
    var options = {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4,
        "shadow": { "enabled": true }
      },
      "edges": {
        "arrows": { "to": { "enabled": true, "scaleFactor": 1.2 } },
        "smooth": { "type": "curvedCW", "roundness": 0.2 },
        "shadow": { "enabled": true, "color": "rgba(239,68,68,0.2)" },
        "font": { "align": "top" }
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -80,
          "centralGravity": 0.02,
          "springLength": 150,
          "springConstant": 0.06
        },
        "minVelocity": 0.5,
        "solver": "forceAtlas2Based",
        "stabilization": { "iterations": 200 }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "zoomView": true,
        "dragView": true
      }
    }
    """)

    filepath = os.path.join(output_dir, f"fraud_ring_{gstin}.html")
    os.makedirs(output_dir, exist_ok=True)
    net.write_html(filepath)
    return filepath
