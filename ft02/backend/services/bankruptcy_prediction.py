import numpy as np

def predict_bankruptcy(data):

    gst_filings = data["gst_filings"]
    transactions = data["upi_transactions"]

    # 📊 GST delay trend
    delays = [f["filing_delay"] for f in gst_filings]
    avg_delay = np.mean(delays)

    # 💰 Transaction trend
    amounts = [t["amount"] for t in transactions]

    if len(amounts) > 1:
        trend = amounts[-1] - amounts[0]
    else:
        trend = 0

    # 📉 Risk calculation
    risk_score = 0

    if avg_delay > 2:
        risk_score += 30

    if trend < 0:
        risk_score += 40

    if len(transactions) < 100:
        risk_score += 30

    probability = min(risk_score, 100)

    # classification
    if probability >= 70:
        status = "HIGH RISK"
    elif probability >= 40:
        status = "MEDIUM RISK"
    else:
        status = "LOW RISK"

    return {
        "bankruptcy_probability": probability,
        "risk_level": status
    }