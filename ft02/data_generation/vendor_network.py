"""
Vendor-Customer Network Generator

Simulates supplier and buyer relationship graphs using NetworkX.
Uses power-law distributions for network size and generates
realistic concentration metrics.
"""

import numpy as np
import networkx as nx
from utils.constants import NETWORK_PARAMS


def _power_law_sample(alpha: float, x_min: int, x_max: int) -> int:
    """Sample from a discrete power-law distribution."""
    u = np.random.random()
    x = int(x_min * (1 - u) ** (-1.0 / (alpha - 1)))
    return min(x, x_max)


def generate_network_data(gstin: str, sector: str,
                          is_fraud: bool = False) -> dict:
    """
    Generate vendor-customer network for a business.

    Args:
        gstin: Business GSTIN (used as node identifier)
        sector: Business sector
        is_fraud: Whether business is fraudulent

    Returns:
        Dict with network metrics and graph structure
    """
    params = NETWORK_PARAMS

    # Generate vendor and customer counts using power law
    vendor_count = _power_law_sample(
        params["vendor_count_alpha"],
        params["vendor_count_min"],
        params["vendor_count_max"],
    )
    customer_count = _power_law_sample(
        params["customer_count_alpha"],
        params["customer_count_min"],
        params["customer_count_max"],
    )

    if is_fraud:
        # Fraudulent businesses tend to have fewer real relationships
        vendor_count = max(2, vendor_count // 2)
        customer_count = max(2, customer_count // 2)

    # ── Build NetworkX graph ────────────────────────────────────────────────
    G = nx.DiGraph()
    G.add_node(gstin, type="target_business", sector=sector)

    # Generate vendor nodes
    vendors = []
    for i in range(vendor_count):
        vid = f"V_{gstin[:8]}_{i:03d}"
        G.add_node(vid, type="vendor")
        # Transaction weight (purchase volume)
        weight = float(np.random.lognormal(mean=10, sigma=1.5))
        G.add_edge(vid, gstin, weight=round(weight, 2), type="supply")
        vendors.append(vid)

    # Generate customer nodes
    customers = []
    customer_revenues = []
    for i in range(customer_count):
        cid = f"C_{gstin[:8]}_{i:03d}"
        G.add_node(cid, type="customer")
        weight = float(np.random.lognormal(mean=10, sigma=1.8))
        G.add_edge(gstin, cid, weight=round(weight, 2), type="sale")
        customers.append(cid)
        customer_revenues.append(weight)

    # ── Customer concentration metrics ──────────────────────────────────────
    total_revenue = sum(customer_revenues) if customer_revenues else 1.0

    # Herfindahl-Hirschman Index (normalized)
    if total_revenue > 0 and len(customer_revenues) > 0:
        shares = [r / total_revenue for r in customer_revenues]
        hhi = sum(s ** 2 for s in shares)
        concentration_ratio = round(float(hhi), 4)

        # Dependency on single customer
        max_share = max(shares)
        dependency_on_single_customer = round(float(max_share), 4)
    else:
        concentration_ratio = 1.0
        dependency_on_single_customer = 1.0

    # ── Inject fraud patterns ───────────────────────────────────────────────
    circular_trades = []
    if is_fraud and np.random.random() < 0.6:
        # Create circular trading pattern
        n_circular = min(3, len(vendors), len(customers))
        for i in range(n_circular):
            # Customer -> Vendor -> Business (circular)
            if i < len(customers) and i < len(vendors):
                G.add_edge(customers[i], vendors[i],
                           weight=round(float(np.random.lognormal(10, 1)), 2),
                           type="circular")
                circular_trades.append({
                    "path": [gstin, customers[i], vendors[i], gstin],
                    "type": "circular_trading"
                })

    # ── Serialize graph data ────────────────────────────────────────────────
    edges_data = []
    for u, v, data in G.edges(data=True):
        edges_data.append({
            "source": u,
            "target": v,
            "weight": data.get("weight", 0),
            "type": data.get("type", "unknown"),
        })

    return {
        "vendor_count": vendor_count,
        "customer_count": customer_count,
        "customer_concentration_ratio": concentration_ratio,
        "dependency_on_single_customer": dependency_on_single_customer,
        "circular_trades": circular_trades,
        "edges": edges_data,
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
    }
