from fastapi import APIRouter, HTTPException
from backend.services.simulation_service import simulate_business_data
from backend.services.feature_engineering import generate_features
from backend.services.credit_scoring import calculate_credit_score, classify_risk, recommend_loan

router = APIRouter()

@router.get("/credit-score/{gstin}")
def credit_score(gstin: str):

    try:
        # Step 1: simulate data
        data = simulate_business_data(gstin)

        # Step 2: features
        features = generate_features(data)

        # Step 3: scoring
        score = calculate_credit_score(features)
        risk = classify_risk(score)
        loan = recommend_loan(score)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "gstin": gstin,
        "score": score,
        "risk": risk,
        "recommended_loan": loan,
        "features": features
    }