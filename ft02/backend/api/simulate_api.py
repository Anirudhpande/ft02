from fastapi import APIRouter
from backend.services.simulation_service import simulate_business_data
from backend.utils.gst_validator import validate_gstin

router = APIRouter()

@router.get("/simulate/{gstin}")
def simulate_data(gstin: str):

    if not validate_gstin(gstin):
        return {"error": "Invalid GSTIN"}

    result = simulate_business_data(gstin)

    return {
        "gstin": gstin,
        "status": result
    }