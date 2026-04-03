"""
Fraud Detection Module

Provides two interfaces for fraud detection:
- detect_fraud(transactions)       — from in-memory list (backward compat)
- detect_fraud_from_db(gstin, db)  — from database (new credit engine)

Uses networkx to build a directed transaction graph and detect
circular patterns (A → B → C → A) indicating potential fraud.
"""

import networkx as nx
from backend.database.db import SessionLocal
from backend.database.models import UPITransaction


def detect_fraud(transactions):
    """
    Detect fraud from an in-memory list of transaction dicts.
    Used by existing /fraud endpoint.
    """

    G = nx.DiGraph()

    for txn in transactions:
        sender = txn["sender"]
        receiver = txn["receiver"]
        amount = txn["amount"]

        G.add_edge(sender, receiver, weight=amount)

    cycles = list(nx.simple_cycles(G))

    fraud_flag = False

    if len(cycles) > 0:
        fraud_flag = True

    return {
        "fraud_detected": fraud_flag,
        "suspicious_cycles": cycles
    }


def detect_fraud_from_db(gstin: str, db=None) -> bool:
    """
    Detect circular transaction fraud for a GSTIN by querying DB.
    Used by the new credit engine pipeline.

    Builds a directed graph from all UPI transactions involving
    this GSTIN and checks for cycles of length >= 2
    (excluding self-loops).

    Args:
        gstin: Business GSTIN identifier
        db: Optional SQLAlchemy session. Creates one if not provided.

    Returns:
        True if circular fraud patterns detected, False otherwise
    """

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # Get all transactions where this GSTIN is sender or receiver
        transactions = db.query(UPITransaction).filter(
            (UPITransaction.sender_gstin == gstin) |
            (UPITransaction.receiver_gstin == gstin)
        ).all()

        if not transactions:
            return False

        # Build directed graph
        G = nx.DiGraph()

        for txn in transactions:
            sender = txn.sender_gstin
            receiver = txn.receiver_gstin

            # Skip self-loops
            if sender == receiver:
                continue

            if G.has_edge(sender, receiver):
                G[sender][receiver]["weight"] += txn.amount
            else:
                G.add_edge(sender, receiver, weight=txn.amount)

        # Detect cycles of length >= 2
        cycles = [c for c in nx.simple_cycles(G) if len(c) >= 2]

        return len(cycles) > 0

    finally:
        if close_db:
            db.close()