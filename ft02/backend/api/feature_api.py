from fastapi import APIRouter
from services.feature_engineering import generate_features
from services.simulation_service import simulate_business_data

router = APIRouter()

@router.get("/features/{gstin}")
def get_features(gstin: str):

    data = simulate_business_data(gstin)

    features = generate_features(data)

    return {
        "gstin": gstin,
        "features": features
    }