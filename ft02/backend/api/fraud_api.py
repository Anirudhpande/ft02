from fastapi import APIRouter
from services.simulation_service import simulate_business_data
from services.fraud_detection import detect_fraud

router = APIRouter()

@router.get("/fraud/{gstin}")
def fraud_check(gstin: str):

    data = simulate_business_data(gstin)

    transactions = data["upi_transactions"]

    result = detect_fraud(transactions)

    return {
        "gstin": gstin,
        "fraud_analysis": result
    }