from fastapi import APIRouter, HTTPException
from backend.services.simulation_service import simulate_business_data
from backend.services.bankruptcy_prediction import predict_bankruptcy

router = APIRouter()

@router.get("/bankruptcy/{gstin}")
def bankruptcy_check(gstin: str):

    try:
        data = simulate_business_data(gstin)
        result = predict_bankruptcy(data)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "gstin": gstin,
        "prediction": result
    }