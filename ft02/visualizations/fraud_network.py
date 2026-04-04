"""
Fraud Network Visualizer

Displays vendor-customer relationship graphs using NetworkX + matplotlib.
Highlights circular trading paths, suspicious dense clusters, and
dependency patterns.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import os


def generate_fraud_network(business: dict, output_dir: str) -> str:
    gstin = business["business_identity"]["gstin"]
    network = business.get("network_data", {})
    edges = network.get("edges", [])
    circular = network.get("circular_trades", [])

    if not edges:
        return ""

    # Build graph
    G = nx.DiGraph()
    G.add_node(gstin, type="target")

    for edge in edges:
        G.add_edge(edge["source"], edge["target"],
                    weight=edge.get("weight", 1),
                    edge_type=edge.get("type", "unknown"))

    if G.number_of_nodes() > 40:
        neighbors = set(G.predecessors(gstin)) | set(G.successors(gstin))
        top_nodes = {gstin} | neighbors
        G = G.subgraph(top_nodes).copy()

    with plt.style.context("dark_background"):
        fig, ax = plt.subplots(figsize=(12, 10))
        fig.patch.set_facecolor('#121212')
        ax.set_facecolor('#121212')

        try:
            pos = nx.spring_layout(G, k=2.5, iterations=60, seed=42)
        except Exception:
            pos = nx.circular_layout(G)

        # ── Color nodes ──────────────────────────────────────────────
        node_colors = []
        node_sizes = []
        node_edge_colors = []
        node_edge_widths = []
        for node in G.nodes():
            if node == gstin:
                node_colors.append("#2196F3")
                node_sizes.append(900)
                node_edge_colors.append("#ffffff")
                node_edge_widths.append(2)
            elif any(node in ct.get("path", []) for ct in circular):
                node_colors.append("#F44336")
                node_sizes.append(600)
                node_edge_colors.append("#FFCDD2")
                node_edge_widths.append(2)
            elif node.startswith("V_"):
                node_colors.append("#4CAF50")
                node_sizes.append(400)
                node_edge_colors.append("#121212")
                node_edge_widths.append(1)
            else:
                node_colors.append("#FF9800")
                node_sizes.append(400)
                node_edge_colors.append("#121212")
                node_edge_widths.append(1)

        # ── Color edges ──────────────────────────────────────────────
        edge_colors = []
        edge_widths = []
        edge_alphas = []
        for u, v, data in G.edges(data=True):
            if data.get("edge_type") == "circular":
                edge_colors.append("#FF5252")
                edge_widths.append(4.0)
                edge_alphas.append(0.9)
            elif data.get("edge_type") == "supply":
                edge_colors.append("#81C784")
                edge_widths.append(1.5)
                edge_alphas.append(0.5)
            else:
                edge_colors.append("#FFB74D")
                edge_widths.append(1.5)
                edge_alphas.append(0.5)

        # Draw Glow for circular edges
        for u, v, data in G.edges(data=True):
            if data.get("edge_type") == "circular":
                nx.draw_networkx_edges(G, pos, edgelist=[(u,v)], ax=ax,
                                       edge_color="#F44336", width=12, alpha=0.15,
                                       arrows=False, connectionstyle="arc3,rad=0.1")
                nx.draw_networkx_edges(G, pos, edgelist=[(u,v)], ax=ax,
                                       edge_color="#F44336", width=8, alpha=0.3,
                                       arrows=False, connectionstyle="arc3,rad=0.1")

        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                                node_size=node_sizes, alpha=0.9,
                                edgecolors=node_edge_colors, linewidths=node_edge_widths)

        nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_colors,
                                width=edge_widths, alpha=edge_alphas,
                                arrows=True, arrowsize=18,
                                connectionstyle="arc3,rad=0.1")

        # Edge labels for circular trades
        edge_labels = {}
        for u, v, data in G.edges(data=True):
            if data.get("edge_type") == "circular":
                amt = 0
                for ct in circular:
                    if u in ct.get("path", []) and v in ct.get("path", []):
                        amt = ct.get("rotated_funds", 0)
                if amt > 0:
                    edge_labels[(u, v)] = f"Rs.{amt:,} Loop"
                    
        if edge_labels:
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax, 
                                         font_color='#FF5252', font_size=11, font_weight='black')

        # Labels (abbreviated)
        labels = {}
        for node in G.nodes():
            if node == gstin:
                labels[node] = "TARGET"
            elif node.startswith("V_"):
                idx = node.split("_")[-1]
                labels[node] = f"V{idx}"
            elif node.startswith("C_"):
                idx = node.split("_")[-1]
                labels[node] = f"C{idx}"
            else:
                labels[node] = node[:6]

        nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=8,
                                 font_weight="bold", font_color="#000000")

        # Legend
        legend_elements = [
            plt.scatter([], [], c="#2196F3", s=150, edgecolors="#ffffff", linewidth=2, label="Target Business"),
            plt.scatter([], [], c="#4CAF50", s=100, label="Vendors"),
            plt.scatter([], [], c="#FF9800", s=100, label="Customers"),
            plt.scatter([], [], c="#F44336", s=150, edgecolors="#FFCDD2", linewidth=2, label="Suspicious Nodes"),
        ]

        if circular:
            legend_elements.append(
                plt.Line2D([0], [0], color="#FF5252", linewidth=4,
                           label=f"Circular Trades ({len(circular)})")
            )

        ax.legend(handles=legend_elements, loc="upper left",
                  fontsize=10, facecolor="#000000", edgecolor="#333333", framealpha=0.8)

        ax.set_title(
            f"Vendor-Customer Network Topology — {business['business_identity']['trade_name']}\n"
            f"({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)",
            fontsize=16, fontweight="bold", color="#ffffff"
        )
        ax.axis("off")

        plt.tight_layout()

        filepath = os.path.join(output_dir, f"network_{gstin}.png")
        fig.savefig(filepath, dpi=300, bbox_inches="tight", facecolor='#121212', transparent=False)
        plt.close(fig)

    return filepath
