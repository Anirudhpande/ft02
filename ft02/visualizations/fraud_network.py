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
    """
    Generate a fraud network visualization.

    Args:
        business: Complete business dictionary
        output_dir: Directory to save the chart

    Returns:
        Path to saved chart image
    """
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

    # Limit to manageable size for visualization
    if G.number_of_nodes() > 40:
        # Keep only nodes directly connected to target + top weight edges
        neighbors = set(G.predecessors(gstin)) | set(G.successors(gstin))
        top_nodes = {gstin} | neighbors
        G = G.subgraph(top_nodes).copy()

    fig, ax = plt.subplots(figsize=(12, 10))

    # Layout
    try:
        pos = nx.spring_layout(G, k=2.0, iterations=50, seed=42)
    except Exception:
        pos = nx.circular_layout(G)

    # ── Color nodes by type ─────────────────────────────────────────────────
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        if node == gstin:
            node_colors.append("#2196F3")
            node_sizes.append(800)
        elif any(node in ct.get("path", []) for ct in circular):
            node_colors.append("#F44336")
            node_sizes.append(400)
        elif node.startswith("V_"):
            node_colors.append("#4CAF50")
            node_sizes.append(300)
        else:
            node_colors.append("#FF9800")
            node_sizes.append(300)

    # ── Color edges by type ─────────────────────────────────────────────────
    edge_colors = []
    edge_widths = []
    for u, v, data in G.edges(data=True):
        if data.get("edge_type") == "circular":
            edge_colors.append("#F44336")
            edge_widths.append(3.0)
        elif data.get("edge_type") == "supply":
            edge_colors.append("#4CAF50")
            edge_widths.append(1.5)
        else:
            edge_colors.append("#FF9800")
            edge_widths.append(1.5)

    # Draw
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                            node_size=node_sizes, alpha=0.9,
                            edgecolors="white", linewidths=2)

    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_colors,
                            width=edge_widths, alpha=0.7,
                            arrows=True, arrowsize=15,
                            connectionstyle="arc3,rad=0.1")

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

    nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=7,
                             font_weight="bold")

    # Legend
    legend_elements = [
        plt.scatter([], [], c="#2196F3", s=100, label="Target Business"),
        plt.scatter([], [], c="#4CAF50", s=80, label="Vendors"),
        plt.scatter([], [], c="#FF9800", s=80, label="Customers"),
        plt.scatter([], [], c="#F44336", s=80, label="Suspicious Nodes"),
    ]

    if circular:
        legend_elements.append(
            plt.Line2D([0], [0], color="#F44336", linewidth=3,
                       label=f"Circular Trades ({len(circular)})")
        )

    ax.legend(handles=legend_elements, loc="upper left",
              fontsize=9, framealpha=0.9)

    ax.set_title(
        f"Vendor-Customer Network — {business['business_identity']['trade_name']}\n"
        f"({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)",
        fontsize=14, fontweight="bold"
    )
    ax.axis("off")

    plt.tight_layout()

    filepath = os.path.join(output_dir, f"network_{gstin}.png")
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return filepath

def generate_fraud_network_html(business: dict, output_dir: str) -> str:
    """
    Generate an interactive PyVis HTML fraud network visualization for the dashboard.
    """
    from pyvis.network import Network
    gstin = business["business_identity"]["gstin"]
    network = business.get("network_data", {})
    edges = network.get("edges", [])
    circular = network.get("circular_trades", [])

    if not edges:
        return ""

    G = nx.DiGraph()
    G.add_node(gstin, type="target")

    for edge in edges:
        G.add_edge(edge["source"], edge["target"],
                    weight=edge.get("weight", 1),
                    edge_type=edge.get("type", "unknown"))

    if G.number_of_nodes() > 80:
        neighbors = set(G.predecessors(gstin)) | set(G.successors(gstin))
        top_nodes = {gstin} | neighbors
        G = G.subgraph(top_nodes).copy()

    net = Network(height="600px", width="100%", directed=True, bgcolor="#1a2235", font_color="white")
    
    cycle_nodes = set()
    cycle_edges = set()
    for cycle in circular:
        path = cycle.get("path", [])
        cycle_nodes.update(path)
        for i in range(len(path) - 1):
            cycle_edges.add((path[i], path[i+1]))

    for node in G.nodes():
        if node == gstin:
            net.add_node(node, label="TARGET", color="#3b82f6", size=30, title=f"TARGET: {node}")
        elif node in cycle_nodes:
            net.add_node(node, label=str(node)[:6], color="#ef4444", size=25, title=f"Risk Entity: {node}")
        elif node.startswith("V_"):
            net.add_node(node, label=str(node), color="#10b981", size=15, title=f"Vendor: {node}")
        else:
            net.add_node(node, label=str(node), color="#f59e0b", size=15, title=f"Customer: {node}")

    for u, v, data in G.edges(data=True):
        amt = data.get("weight", 0)
        title = f"Amount: Rs. {amt}"
        
        if (u, v) in cycle_edges:
            net.add_edge(u, v, title=title, weight=amt, color="#ef4444", width=3)
        elif data.get("edge_type") == "supply":
            net.add_edge(u, v, title=title, weight=amt, color="#10b981", width=1.5)
        else:
            net.add_edge(u, v, title=title, weight=amt, color="#f59e0b", width=1.5)

    net.set_options(\"""
    var options = {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4
      },
      "edges": {
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.5
          }
        },
        "smooth": {
          "type": "continuous",
          "forceDirection": "none"
        }
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "minVelocity": 0.75,
        "solver": "forceAtlas2Based"
      }
    }
    \""")
    
    filepath = os.path.join(output_dir, f"network_int_{gstin}.html")
    net.write_html(filepath)
    return filepath
