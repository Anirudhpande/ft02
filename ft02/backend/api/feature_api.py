from fastapi import APIRouter, HTTPException
from backend.services.feature_engineering import generate_features
from backend.services.simulation_service import simulate_business_data

router = APIRouter()

@router.get("/features/{gstin}")
def get_features(gstin: str):

    try:
        data = simulate_business_data(gstin)
        features = generate_features(data)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "gstin": gstin,
        "features": features
    }