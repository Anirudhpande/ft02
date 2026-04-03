import networkx as nx
import numpy as np

def detect_fraud_rings(edges_data, target_node):
    """
    Detect closed-loop money rotation patterns (fraud rings) using NetworkX.
    Takes a list of transaction edges and builds a directed graph.
    Returns a list of detected circular trade paths that involve the target_node
    or have suspicious properties.
    """
    G = nx.DiGraph()
    
    # Add all edges
    for edge in edges_data:
        G.add_edge(edge["source"], edge["target"], 
                   weight=edge.get("weight", 1.0),
                   edge_type=edge.get("type", "unknown"))

    detected_cycles = []
    
    # Use NetworkX to find simple cycles
    try:
        # Find all simple cycles (closed loops) in the directed graph
        cycles = list(nx.simple_cycles(G))
        
        for cycle in cycles:
            # We are interested in cycles that involve multiple independent entities
            # typically length >= 2
            if len(cycle) > 2 or (len(cycle) == 2 and set(cycle) != {target_node}):
                # Get total funds moving through this cycle
                # We can determine the minimum weight flowing through the loop
                cycle_edges = []
                cycle_weights = []
                for i in range(len(cycle)):
                    u = cycle[i]
                    v = cycle[(i + 1) % len(cycle)] # wrap around
                    edge_data = G.get_edge_data(u, v)
                    cycle_edges.append((u, v))
                    if edge_data and "weight" in edge_data:
                        cycle_weights.append(edge_data["weight"])
                
                # Minimum weight transfer in the cycle is the "rotated amount"
                rotated_funds = min(cycle_weights) if cycle_weights else 0
                
                # Check if this loop is a significant fraud ring
                if rotated_funds > 0:
                    detected_cycles.append({
                        "path": cycle + [cycle[0]], # closed loop representation
                        "type": "circular_trading",
                        "rotated_funds": rotated_funds
                    })
    except Exception as e:
        print(f"Error detecting fraud rings: {e}")
        pass

    return detected_cycles
