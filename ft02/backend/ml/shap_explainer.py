"""
SHAP Explainability Module (Placeholder)

This module provides scaffold code for generating SHAP-based
explanations for ML credit scoring predictions.

Future implementation will integrate with the trained XGBoost model
from train_model.py to provide feature importance analysis.
"""

import pandas as pd


def explain_prediction(model, features: dict) -> dict:
    """
    Generate SHAP-based explanation for a credit prediction.

    Args:
        model: Trained ML model (e.g., XGBoost)
        features: Feature dictionary from extract_features_from_db

    Returns:
        Dictionary with feature importances and explanation text
    """
    try:
        import shap

        feature_cols = [
            "avg_filing_delay",
            "total_upi_volume",
            "shipment_count",
            "avg_transaction_value",
            "transaction_count"
        ]

        df = pd.DataFrame([features])
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(df[feature_cols])

        # Map SHAP values to feature names
        importance = {}
        for i, col in enumerate(feature_cols):
            importance[col] = float(shap_values[0][i])

        # Sort by absolute importance
        sorted_features = sorted(
            importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )

        # Generate human-readable reasons
        reasons = []
        for feature_name, shap_value in sorted_features[:5]:
            direction = "positively" if shap_value > 0 else "negatively"
            readable_name = feature_name.replace("_", " ").title()
            reasons.append(f"{readable_name} {direction} impacts credit score")

        return {
            "shap_values": importance,
            "top_reasons": reasons
        }

    except ImportError:
        return {
            "shap_values": {},
            "top_reasons": ["SHAP library not installed — using rule-based explanations"]
        }
