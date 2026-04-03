"""
SHAP Explainability Module

Generates per-feature SHAP importance values for both credit scoring
and fraud detection models using TreeExplainer.
"""

import numpy as np
import pandas as pd


def explain_credit_score(business: dict, credit_models: dict) -> dict:
    """
    Generate SHAP explanation for a credit score prediction.

    Args:
        business: Complete business dictionary (with _credit_features)
        credit_models: Dict with 'xgb_model' and 'feature_columns'

    Returns:
        Dict with 'shap_values', 'top_positive', 'top_negative'
    """
    try:
        import shap
    except ImportError:
        return _fallback_credit_explanation(business)

    model = credit_models["xgb_model"]
    feature_cols = credit_models["feature_columns"]
    features = business.get("_credit_features", {})

    feature_values = [features.get(col, 0.0) for col in feature_cols]
    X = pd.DataFrame([feature_values], columns=feature_cols)

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        # Handle different SHAP output formats
        if isinstance(shap_values, list):
            sv = shap_values[0]
        elif hasattr(shap_values, 'values'):
            sv = shap_values.values[0]
        else:
            sv = shap_values[0]

        # Map to feature names
        importance = {}
        for i, col in enumerate(feature_cols):
            importance[col] = float(sv[i]) if i < len(sv) else 0.0

        # Sort by absolute value
        sorted_feats = sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True)

        top_positive = [(k, v) for k, v in sorted_feats if v > 0][:5]
        top_negative = [(k, v) for k, v in sorted_feats if v < 0][:5]

        return {
            "shap_values": importance,
            "top_positive_factors": top_positive,
            "top_negative_factors": top_negative,
            "method": "shap_tree",
        }

    except Exception as e:
        print(f"[SHAP] Warning: TreeExplainer failed ({e}), using fallback")
        return _fallback_credit_explanation(business)


def explain_fraud_prediction(business: dict, fraud_models: dict) -> dict:
    """
    Generate SHAP explanation for a fraud prediction.

    Args:
        business: Complete business dictionary
        fraud_models: Dict with 'rf_model' and 'feature_columns'

    Returns:
        Dict with 'shap_values', 'top_risk_factors'
    """
    try:
        import shap
    except ImportError:
        return _fallback_fraud_explanation(business)

    model = fraud_models["rf_model"]
    feature_cols = fraud_models["feature_columns"]
    features = business.get("_fraud_features", {})

    if not features:
        from fraud_detection.fraud_features import build_fraud_features
        features = build_fraud_features(business)

    feature_values = [features.get(col, 0.0) for col in feature_cols]
    X = pd.DataFrame([feature_values], columns=feature_cols)

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        # For classifiers, SHAP returns [class_0, class_1]
        if isinstance(shap_values, list) and len(shap_values) > 1:
            sv = shap_values[1][0]  # Class 1 (fraud)
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            sv = shap_values[0, :, 1]
        elif hasattr(shap_values, 'values'):
            sv = shap_values.values[0]
        else:
            sv = shap_values[0] if isinstance(shap_values, np.ndarray) else shap_values

        importance = {}
        for i, col in enumerate(feature_cols):
            importance[col] = float(sv[i]) if i < len(sv) else 0.0

        sorted_feats = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        top_risk = [(k, v) for k, v in sorted_feats if v > 0][:7]

        return {
            "shap_values": importance,
            "top_risk_factors": top_risk,
            "method": "shap_tree",
        }

    except Exception as e:
        print(f"[SHAP] Warning: Fraud explainer failed ({e}), using fallback")
        return _fallback_fraud_explanation(business)


def _fallback_credit_explanation(business: dict) -> dict:
    """Rule-based fallback when SHAP is unavailable."""
    features = business.get("_credit_features", {})
    positives = []
    negatives = []

    if features.get("repayment_ratio", 0) > 0.8:
        positives.append(("repayment_ratio", 0.15))
    else:
        negatives.append(("repayment_ratio", -0.10))

    if features.get("gst_compliance_score", 0) > 0.7:
        positives.append(("gst_compliance_score", 0.12))
    else:
        negatives.append(("gst_compliance_score", -0.08))

    if features.get("turnover_stability", 0) > 0.6:
        positives.append(("turnover_stability", 0.10))
    else:
        negatives.append(("turnover_stability", -0.07))

    return {
        "shap_values": {},
        "top_positive_factors": positives,
        "top_negative_factors": negatives,
        "method": "rule_based_fallback",
    }


def _fallback_fraud_explanation(business: dict) -> dict:
    """Rule-based fallback for fraud explanation."""
    features = business.get("_fraud_features", {})
    risk_factors = []

    if features.get("circular_trade_flag", 0):
        risk_factors.append(("circular_trade_flag", 0.25))
    if features.get("gst_cancellation", 0):
        risk_factors.append(("gst_cancellation", 0.20))
    if features.get("spike_count", 0) > 0:
        risk_factors.append(("spike_count", 0.15))
    if features.get("ps_mismatch", 0) > 0.1:
        risk_factors.append(("ps_mismatch", 0.12))

    return {
        "shap_values": {},
        "top_risk_factors": risk_factors,
        "method": "rule_based_fallback",
    }
