import random
from backend.database.db import SessionLocal
from backend.database.models import Business, GSTFiling, UPITransaction, EWayShipment


def simulate_business_data(gstin):

    db = SessionLocal()

    try:

        business = db.query(Business).filter(Business.gstin == gstin).first()

        if not business:
            business = Business(
                gstin=gstin,
                business_name="Demo MSME",
                state="Maharashtra",
                industry="Manufacturing",
                registration_year=2020,
                business_age=4
            )
            db.add(business)
            db.commit()

        suppliers = db.query(Business).filter(Business.gstin.like("BIZ%")).all()

        if len(suppliers) == 0:

            supplier_list = []

            for i in range(1, 21):

                supplier = Business(
                    gstin=f"BIZ{i}",
                    business_name=f"Supplier {i}",
                    state="Maharashtra",
                    industry="Trading",
                    registration_year=2018,
                    business_age=6
                )

                supplier_list.append(supplier)

            db.add_all(supplier_list)
            db.commit()

        all_businesses = db.query(Business.gstin).all()
        gstins = [b[0] for b in all_businesses]

        filings = []

        for i in range(12):

            filing = GSTFiling(
                gstin=gstin,
                month=f"2024-{i+1}",
                filing_delay_days=random.randint(-2, 5),
                invoice_count=random.randint(50, 200),
                sales_value=random.randint(100000, 400000)
            )

            filings.append(filing)

        db.add_all(filings)

        transactions = []

        for i in range(200):

            receiver = random.choice(gstins)

            txn = UPITransaction(
                sender_gstin=gstin,
                receiver_gstin=receiver,
                amount=random.randint(500, 10000)
            )

            transactions.append(txn)

        db.add_all(transactions)

        shipments = []

        for i in range(20):

            shipment = EWayShipment(
                gstin=gstin,
                origin="Pune",
                destination="Mumbai",
                shipment_value=random.randint(10000, 50000)
            )

            shipments.append(shipment)

        db.add_all(shipments)

        db.commit()

        # Return structured data for downstream services
        return {
            "gst_filings": [
                {
                    "filing_delay": f.filing_delay_days,
                    "sales_value": f.sales_value,
                    "invoice_count": f.invoice_count,
                    "month": f.month
                }
                for f in filings
            ],
            "upi_transactions": [
                {
                    "sender": t.sender_gstin,
                    "receiver": t.receiver_gstin,
                    "amount": t.amount
                }
                for t in transactions
            ],
            "eway_shipments": [
                {
                    "origin": s.origin,
                    "destination": s.destination,
                    "shipment_value": s.shipment_value
                }
                for s in shipments
            ]
        }

    except Exception as e:

        db.rollback()
        raise RuntimeError(f"Simulation failed: {str(e)}")

    finally:

        db.close()