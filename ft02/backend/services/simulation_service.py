import random

def simulate_business_data(gstin):

    gst_filings = []

    for i in range(12):
        gst_filings.append({
            "month": i+1,
            "invoice_count": random.randint(50,200),
            "filing_delay": random.randint(-2,5),
            "sales_value": random.randint(100000,400000)
        })

    upi_transactions = []

    for i in range(200):
        upi_transactions.append({
            "sender": gstin,
            "receiver": f"BIZ{random.randint(1,20)}",
            "amount": random.randint(500,10000)
        })

    shipments = []

    for i in range(20):
        shipments.append({  
            "origin": "Pune",
            "destination": "Mumbai",
            "value": random.randint(10000,50000)
        })

    return {
        "gst_filings": gst_filings,
        "upi_transactions": upi_transactions,
        "eway_shipments": shipments
    }