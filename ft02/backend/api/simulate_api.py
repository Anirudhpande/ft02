from fastapi import APIRouter, HTTPException
from backend.services.simulation_service import simulate_business_data
from backend.utils.gst_validator import validate_gstin

router = APIRouter()

@router.get("/simulate/{gstin}")
def simulate_data(gstin: str):

    if not validate_gstin(gstin):
        raise HTTPException(status_code=400, detail="Invalid GSTIN format")

    try:
        result = simulate_business_data(gstin)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "gstin": gstin,
        "status": "Simulation data generated successfully",
        "summary": {
            "gst_filings_count": len(result["gst_filings"]),
            "upi_transactions_count": len(result["upi_transactions"]),
            "eway_shipments_count": len(result["eway_shipments"])
        }
    }