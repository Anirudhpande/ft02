from fastapi import APIRouter, HTTPException
from backend.services.simulation_service import simulate_business_data
from backend.services.fraud_detection import detect_fraud

router = APIRouter()

@router.get("/fraud/{gstin}")
def fraud_check(gstin: str):

    try:
        data = simulate_business_data(gstin)
        transactions = data["upi_transactions"]
        result = detect_fraud(transactions)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "gstin": gstin,
        "fraud_analysis": result
    }