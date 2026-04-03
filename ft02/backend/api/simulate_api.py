from fastapi import APIRouter
from backend.services.simulation_service import simulate_business_data

router = APIRouter()

@router.get("/simulate/{gstin}")
def simulate_data(gstin: str):

    data = simulate_business_data(gstin)

    return {
        "gstin": gstin,
        "data": data
    }