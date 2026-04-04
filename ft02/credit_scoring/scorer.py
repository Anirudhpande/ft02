"""
Credit Scorer

Uses trained ML models to predict creditworthiness and map to
a 300-900 credit score range.
"""

import warnings
import numpy as np
import pandas as pd
from credit_scoring.feature_builder import build_credit_features, get_feature_columns
from utils.constants import CREDIT_SCORE_MIN, CREDIT_SCORE_MAX


def score_business(business: dict, models: dict, adjustment_strategy: str = "feature_level") -> dict:
    """
    Calculate credit score for a single business.

    Args:
        business: Complete business dictionary
        models: Dict with 'xgb_model', 'lgbm_model', 'feature_columns'
        adjustment_strategy: "feature_level" or "score_level"

    Returns:
        Dict with 'credit_score', 'probability', and feature values
    """
    # Extract features
    features = build_credit_features(business, amnesty_strategy=adjustment_strategy)
    feature_cols = models["feature_columns"]

    # Build feature DataFrame (preserves column names for LightGBM)
    feature_values = [features.get(col, 0.0) for col in feature_cols]
    X = pd.DataFrame([feature_values], columns=feature_cols)

    # Predict with ensemble
    xgb_model = models["xgb_model"]
    xgb_prob = float(xgb_model.predict(X)[0])

    lgbm_model = models.get("lgbm_model")
    if lgbm_model is not None:
        lgbm_prob = float(lgbm_model.predict(X)[0])
        # Weighted average (XGBoost 60%, LightGBM 40%)
        probability = 0.6 * xgb_prob + 0.4 * lgbm_prob
    else:
        probability = xgb_prob

    # Clip probability
    probability = np.clip(probability, 0.0, 1.0)

    # Map to credit score range
    score = int(round(CREDIT_SCORE_MIN + probability * (CREDIT_SCORE_MAX - CREDIT_SCORE_MIN)))
    
    # ── Amnesty Score-Level Calibration ─────────────────────────────────────
    if adjustment_strategy == "score_level":
        from utils.amnesty_config import is_any_amnesty_active
        if is_any_amnesty_active() or business.get("_amnesty_active_override", False):
            # Calibrate score upwards since base model already penalised late filings
            late = business.get("gst_behavior", {}).get("late_filings_count", 0)
            months = business.get("gst_behavior", {}).get("months_not_filed", 0)
            
            penalty_relief = min(150, (late * 10) + (months * 15))
            score += penalty_relief

    score = max(CREDIT_SCORE_MIN, min(CREDIT_SCORE_MAX, score))

    return {
        "credit_score": score,
        "probability": round(float(probability), 4),
        "features": features,
    }


def score_all_businesses(businesses: list, models: dict) -> list:
    """
    Score all businesses in the dataset.

    Args:
        businesses: List of business dictionaries
        models: Trained model dictionary

    Returns:
        Updated businesses list with credit scores
    """
    print(f"[Scorer] Scoring {len(businesses)} businesses...")

    scores = []
    for i, biz in enumerate(businesses):
        result = score_business(biz, models)
        biz["credit_score"] = result["credit_score"]
        biz["_credit_features"] = result["features"]
        biz["_credit_probability"] = result["probability"]
        scores.append(result["credit_score"])

    scores_arr = np.array(scores)
    print(f"[Scorer] Score distribution: "
          f"min={scores_arr.min()}, max={scores_arr.max()}, "
          f"mean={scores_arr.mean():.0f}, median={np.median(scores_arr):.0f}")

    return businesses


def classify_risk_band(score: int) -> str:
    """Classify credit score into risk band."""
    if score >= 750:
        return "LOW RISK"
    elif score >= 650:
        return "MEDIUM RISK"
    elif score >= 500:
        return "HIGH RISK"
    else:
        return "VERY HIGH RISK"
