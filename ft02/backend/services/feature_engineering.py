"""
Feature Engineering Module

Provides two interfaces for feature extraction:
- generate_features(data)         — from in-memory dict (backward compat)
- extract_features_from_db(gstin) — from database (new credit engine)
"""

import numpy as np
from backend.database.db import SessionLocal
from backend.database.models import GSTFiling, UPITransaction, EWayShipment


def generate_features(data):
    """
    Generate features from an in-memory data dict.
    Used by existing /features and legacy /credit-score endpoints.
    """

    gst_filings = data["gst_filings"]
    transactions = data["upi_transactions"]
    shipments = data["eway_shipments"]

    # GST Features
    delays = [f["filing_delay"] for f in gst_filings]
    sales = [f["sales_value"] for f in gst_filings]

    avg_delay = np.mean(delays)
    sales_variance = np.var(sales)

    # Transaction Features
    amounts = [t["amount"] for t in transactions]

    total_txn = len(transactions)
    avg_txn_value = np.mean(amounts)

    # Shipment Features
    shipment_count = len(shipments)

    features = {
        "avg_filing_delay": avg_delay,
        "sales_variance": sales_variance,
        "transaction_count": total_txn,
        "avg_transaction_value": avg_txn_value,
        "shipment_count": shipment_count
    }

    return features


def extract_features_from_db(gstin: str, db=None) -> dict:
    """
    Extract features directly from the database for a given GSTIN.
    Used by the new credit engine pipeline.

    Args:
        gstin: Business GSTIN identifier
        db: Optional SQLAlchemy session. Creates one if not provided.

    Returns:
        Feature dictionary with: avg_filing_delay, total_upi_volume,
        shipment_count, avg_transaction_value, transaction_count
    """

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # GST Filing Features
        filings = db.query(GSTFiling).filter(GSTFiling.gstin == gstin).all()

        if filings:
            delays = [f.filing_delay_days for f in filings]
            avg_filing_delay = float(np.mean(delays))
        else:
            avg_filing_delay = 0.0

        # UPI Transaction Features
        transactions = db.query(UPITransaction).filter(
            UPITransaction.sender_gstin == gstin
        ).all()

        if transactions:
            amounts = [t.amount for t in transactions]
            total_upi_volume = float(sum(amounts))
            avg_transaction_value = float(np.mean(amounts))
            transaction_count = len(transactions)
        else:
            total_upi_volume = 0.0
            avg_transaction_value = 0.0
            transaction_count = 0

        # E-Way Shipment Features
        shipments = db.query(EWayShipment).filter(
            EWayShipment.gstin == gstin
        ).all()

        shipment_count = len(shipments)

        return {
            "avg_filing_delay": avg_filing_delay,
            "total_upi_volume": total_upi_volume,
            "shipment_count": shipment_count,
            "avg_transaction_value": avg_transaction_value,
            "transaction_count": transaction_count
        }

    finally:
        if close_db:
            db.close()