import numpy as np

def generate_features(data):

    gst_filings = data["gst_filings"]
    transactions = data["upi_transactions"]
    shipments = data["eway_shipments"]

    # 📊 1. GST Features
    delays = [f["filing_delay"] for f in gst_filings]
    sales = [f["sales_value"] for f in gst_filings]

    avg_delay = np.mean(delays)
    sales_variance = np.var(sales)

    # 💰 2. Transaction Features
    amounts = [t["amount"] for t in transactions]

    total_txn = len(transactions)
    avg_txn_value = np.mean(amounts)

    # 🚚 3. Shipment Features
    shipment_count = len(shipments)

    # 📈 Final Feature Vector
    features = {
        "avg_filing_delay": avg_delay,
        "sales_variance": sales_variance,
        "transaction_count": total_txn,
        "avg_transaction_value": avg_txn_value,
        "shipment_count": shipment_count
    }

    return features