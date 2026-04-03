from fastapi import APIRouter
from services.simulation_service import simulate_business_data
from services.feature_engineering import generate_features
from services.credit_scoring import calculate_credit_score, classify_risk, recommend_loan

router = APIRouter()

@router.get("/credit-score/{gstin}")
def credit_score(gstin: str):

    # Step 1: simulate data
    data = simulate_business_data(gstin)

    # Step 2: features
    features = generate_features(data)

    # Step 3: scoring
    score = calculate_credit_score(features)

    risk = classify_risk(score)

    loan = recommend_loan(score)

    return {
        "gstin": gstin,
        "score": score,
        "risk": risk,
        "recommended_loan": loan,
        "features": features
    }