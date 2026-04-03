from fastapi import APIRouter
from services.simulation_service import simulate_business_data
from services.bankruptcy_prediction import predict_bankruptcy

router = APIRouter()

@router.get("/bankruptcy/{gstin}")
def bankruptcy_check(gstin: str):

    data = simulate_business_data(gstin)

    result = predict_bankruptcy(data)

    return {
        "gstin": gstin,
        "prediction": result
    }