import networkx as nx

def detect_fraud(transactions):

    G = nx.DiGraph()

    # Build graph
    for txn in transactions:
        sender = txn["sender"]
        receiver = txn["receiver"]
        amount = txn["amount"]

        G.add_edge(sender, receiver, weight=amount)

    # Detect cycles
    cycles = list(nx.simple_cycles(G))

    fraud_flag = False

    if len(cycles) > 0:
        fraud_flag = True

    return {
        "fraud_detected": fraud_flag,
        "suspicious_cycles": cycles
    }