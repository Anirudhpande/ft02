import networkx as nx
import numpy as np
import datetime
from pyvis.network import Network
import os

def detect_fraud_rings(edges_data, target_node):
    """
    Backwards compatibility for existing API calls without full transaction timestamps.
    """
    G = nx.DiGraph()
    for edge in edges_data:
        G.add_edge(edge["source"], edge["target"], 
                   weight=edge.get("weight", 1.0),
                   edge_type=edge.get("type", "unknown"))

    detected_cycles = []
    try:
        cycles = list(nx.simple_cycles(G))
        for cycle in cycles:
            if len(cycle) > 2 or (len(cycle) == 2 and set(cycle) != {target_node}):
                cycle_weights = []
                for i in range(len(cycle)):
                    u = cycle[i]
                    v = cycle[(i + 1) % len(cycle)]
                    edge_data = G.get_edge_data(u, v)
                    if edge_data and "weight" in edge_data:
                        cycle_weights.append(edge_data["weight"])
                
                rotated_funds = min(cycle_weights) if cycle_weights else 0
                if rotated_funds > 0:
                    detected_cycles.append({
                        "path": cycle + [cycle[0]],
                        "type": "circular_trading",
                        "rotated_funds": rotated_funds
                    })
    except Exception as e:
        pass
    return detected_cycles

def check_time_amount_constraints(cycle_edges, time_window_hours=48, amount_variance_threshold=0.2):
    """
    Verify if a cycle is fraudulent based on strict time boundaries and amount similarities.
    Transactions must happen within `time_window_hours` and have similar amounts.
    """
    if not cycle_edges:
        return False, 0
    
    times = []
    amounts = []
    for edge in cycle_edges:
        if "timestamp" in edge:
            if isinstance(edge["timestamp"], str):
                try:
                    dt = datetime.datetime.fromisoformat(edge["timestamp"])
                    times.append(dt)
                except:
                    pass
            elif isinstance(edge["timestamp"], datetime.datetime):
                times.append(edge["timestamp"])
        if "amount" in edge:
            amounts.append(float(edge["amount"]))
            
    # Time constraint
    time_constraint_met = True
    if times and len(times) == len(cycle_edges):
        time_diff = max(times) - min(times)
        if time_diff.total_seconds() / 3600 > time_window_hours:
            time_constraint_met = False

    # Amount similarity constraint
    amt_similarity_met = True
    amount_variance = 0
    if amounts:
        avg_amt = np.mean(amounts)
        max_diff = max([abs(a - avg_amt) for a in amounts]) / max(avg_amt, 1)
        amount_variance = max_diff
        if max_diff > amount_variance_threshold:
            amt_similarity_met = False
            
    # Score calculation
    score = 0.5
    if time_constraint_met and len(times) == len(cycle_edges):
        score += 0.25
    if amt_similarity_met and len(amounts) == len(cycle_edges):
        score += 0.25
        
    # Deduct score if high variance
    score -= min(0.3, amount_variance)
    return True, max(0, min(1.0, score))


def analyze_transaction_network(transactions, time_window_hours=48):
    """
    Advanced fraud detection (Twist 1).
    Takes a list of dicts: {"sender": GSTIN, "receiver": GSTIN, "amount": float, "timestamp": string}
    """
    G = nx.MultiDiGraph() # Allow multiple transactions between same entities
    
    for tx in transactions:
        sender = tx.get("sender") or tx.get("source")
        receiver = tx.get("receiver") or tx.get("target")
        amt = float(tx.get("amount", tx.get("weight", 0)))
        ts = tx.get("timestamp")
        if sender and receiver:
            G.add_edge(sender, receiver, amount=amt, timestamp=ts)

    # To find cycles easily, project to simple DiGraph
    simple_G = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        if not simple_G.has_edge(u, v):
            simple_G.add_edge(u, v, transactions=[])
        simple_G[u][v]["transactions"].append(data)

    detected_rings = []
    involved_entites = set()
    total_fraud_score = 0
    cycle_freq = {}
    
    try:
        cycles = list(nx.simple_cycles(simple_G))
        for cycle in cycles:
            if len(cycle) >= 2:
                # Find matching sequence of transactions that form this loop
                cycle_txs = []
                for i in range(len(cycle)):
                    u = cycle[i]
                    v = cycle[(i + 1) % len(cycle)]
                    # Just take the first transaction for simplicity, or ideally find the chronologically valid one
                    txs = simple_G[u][v]["transactions"]
                    if txs:
                        cycle_txs.append(txs[0])
                
                is_valid, cycle_score = check_time_amount_constraints(cycle_txs, time_window_hours)
                
                # Frequency
                cycle_tuple = tuple(sorted(cycle))
                cycle_freq[cycle_tuple] = cycle_freq.get(cycle_tuple, 0) + 1
                if cycle_freq[cycle_tuple] > 1:
                    cycle_score = min(1.0, cycle_score + 0.2) # Bonus for frequency
                
                if is_valid and cycle_score > 0.4:
                    rotated_funds = min([tx.get("amount", 0) for tx in cycle_txs]) if cycle_txs else 0
                    detected_rings.append({
                        "path": cycle + [cycle[0]],
                        "score": round(cycle_score, 2),
                        "rotated_amount": rotated_funds
                    })
                    involved_entites.update(cycle)
                    total_fraud_score = max(total_fraud_score, cycle_score)
                    
    except Exception as e:
        print(f"Error in analyze_transaction_network: {e}")

    fraud_flag = total_fraud_score >= 0.7 or len(detected_rings) > 0
    
    return {
        "fraud_flag": fraud_flag,
        "fraud_score": round(total_fraud_score, 2),
        "fraud_type": "circular_transactions" if fraud_flag else "none",
        "involved_entities": list(involved_entites),
        "detected_cycles": detected_rings,
        "graph": G
    }

def generate_interactive_pyvis(G, detected_cycles, output_filepath="static/fraud_graph.html"):
    """
    Generate an interactive PyVis network graph.
    """
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    net = Network(height="600px", width="100%", directed=True, bgcolor="#ffffff", font_color="black")
    
    # Identify nodes in cycles
    cycle_nodes = set()
    cycle_edges = set()
    for cycle in detected_cycles:
        path = cycle.get("path", [])
        cycle_nodes.update(path)
        for i in range(len(path) - 1):
            cycle_edges.add((path[i], path[i+1]))

    # Add Nodes
    for node in G.nodes():
        if node in cycle_nodes:
            net.add_node(node, label=str(node), color="#F44336", size=25, title=f"Risk Entity: {node}")
        else:
            net.add_node(node, label=str(node), color="#4CAF50", size=15, title=f"Entity: {node}")

    # Add Edges
    for u, v, data in G.edges(data=True):
        amt = data.get("amount", 0)
        ts = data.get("timestamp", "-")
        title = f"Amount: {amt}\nTime: {ts}"
        
        if (u, v) in cycle_edges:
            net.add_edge(u, v, title=title, weight=amt, color="#F44336", width=3, label=str(amt))
        else:
            net.add_edge(u, v, title=title, weight=amt, color="#A7A7A7", width=1)
            
    # Options
    net.set_options("""
    var options = {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4
      },
      "edges": {
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 1
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
    """)
    net.write_html(output_filepath)
    return output_filepath

