"""
Credit Score API

Endpoint: GET /credit-score/{gstin}

Pipeline:
1. Extract features from DB
2. Calculate credit score with reasons
3. Detect fraud from DB
4. Compute risk band + loan recommendation
5. Return enriched JSON response
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from backend.database.db import SessionLocal
from backend.services.feature_engineering import extract_features_from_db
from backend.services.scoring_service import (
    calculate_credit_score,
    classify_risk_band,
    recommend_loan_amount
)
from backend.services.fraud_detection import detect_fraud_from_db

router = APIRouter()


@router.get("/credit-score/{gstin}")
def credit_score(gstin: str):

    db = SessionLocal()

    try:
        # Step 1: Extract features from database
        features = extract_features_from_db(gstin, db)

        # Step 2: Calculate credit score + reasons
        result = calculate_credit_score(features)
        score = result["score"]
        top_reasons = result["reasons"]

        # Step 3: Detect fraud
        fraud_flag = detect_fraud_from_db(gstin, db)

        # Apply fraud penalty
        if fraud_flag:
            score = max(300, score - 100)
            top_reasons.insert(0, "Circular transaction pattern detected — fraud risk")

        # Step 4: Classify risk band
        risk_band = classify_risk_band(score)

        # Step 5: Recommend loan amount
        recommended_loan = recommend_loan_amount(score)

        # Step 6: Return enriched response
        return {
            "gstin": gstin,
            "credit_score": score,
            "risk_band": risk_band,
            "recommended_loan": recommended_loan,
            "top_reasons": top_reasons[:5],
            "fraud_flag": fraud_flag,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Credit scoring failed: {str(e)}")

    finally:
        db.close()