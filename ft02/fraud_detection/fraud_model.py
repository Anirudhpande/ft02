"""
Fraud Detection Model

Trains and applies fraud detection models:
- Random Forest Classifier (primary supervised)
- Isolation Forest (unsupervised anomaly detection)
- XGBoost Classifier (ensemble member)

Outputs fraud_probability (0 to 1) per business.
"""

import warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import cross_val_score
from fraud_detection.fraud_features import build_fraud_features, get_fraud_feature_columns


def train_fraud_model(businesses: list) -> dict:
    """
    Train fraud detection models on the business dataset.

    Uses the ground-truth fraud_label for supervised training
    and Isolation Forest for unsupervised anomaly scoring.

    Args:
        businesses: List of business dicts (with fraud_label)

    Returns:
        Dict with 'rf_model', 'iso_model', 'xgb_model', 'feature_columns'
    """
    from xgboost import XGBClassifier

    feature_cols = get_fraud_feature_columns()

    # Build feature matrix
    features_list = []
    labels = []

    for biz in businesses:
        f = build_fraud_features(biz)
        features_list.append(f)
        labels.append(biz.get("fraud_label", 0))
        biz["_fraud_features"] = f

    df = pd.DataFrame(features_list)
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0.0

    X = df[feature_cols].fillna(0).values
    y = np.array(labels)

    print(f"[FraudModel] Training on {len(y)} samples "
          f"(fraud: {sum(y)}, legitimate: {len(y) - sum(y)})")

    # ── Random Forest ───────────────────────────────────────────────────────
    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_split=5,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    rf_model.fit(X, y)

    n_cv = min(5, max(2, len(y) // 5))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rf_cv = cross_val_score(rf_model, X, y, cv=n_cv, scoring="f1")
    print(f"[FraudModel] Random Forest CV F1: {np.mean(rf_cv):.4f} ± {np.std(rf_cv):.4f}")

    # ── Isolation Forest ────────────────────────────────────────────────────
    iso_model = IsolationForest(
        n_estimators=200,
        contamination=0.18,
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    iso_model.fit(X)

    # ── XGBoost Classifier ──────────────────────────────────────────────────
    fraud_ratio = max(sum(y), 1) / max(len(y) - sum(y), 1)
    xgb_model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=1.0 / max(fraud_ratio, 0.01),
        random_state=42,
        eval_metric="logloss",
    )
    xgb_model.fit(X, y)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        xgb_cv = cross_val_score(xgb_model, X, y, cv=n_cv, scoring="f1")
    print(f"[FraudModel] XGBoost CV F1: {np.mean(xgb_cv):.4f} ± {np.std(xgb_cv):.4f}")

    return {
        "rf_model": rf_model,
        "iso_model": iso_model,
        "xgb_model": xgb_model,
        "feature_columns": feature_cols,
        "rf_cv_f1": float(np.mean(rf_cv)),
        "xgb_cv_f1": float(np.mean(xgb_cv)),
    }


def predict_fraud(business: dict, models: dict) -> dict:
    """
    Predict fraud probability for a single business.

    Combines Random Forest, Isolation Forest, and XGBoost predictions
    into a weighted ensemble.

    Args:
        business: Complete business dictionary
        models: Trained fraud model dictionary

    Returns:
        Dict with 'fraud_probability' and individual model scores
    """
    feature_cols = models["feature_columns"]
    features = build_fraud_features(business)

    feature_values = [features.get(col, 0.0) for col in feature_cols]
    X = np.array([feature_values])

    # Random Forest probability
    rf_prob = float(models["rf_model"].predict_proba(X)[0][1])

    # XGBoost probability
    xgb_prob = float(models["xgb_model"].predict_proba(X)[0][1])

    # Isolation Forest anomaly score (convert to probability-like)
    iso_score = float(models["iso_model"].decision_function(X)[0])
    # Isolation Forest: more negative = more anomalous
    # Map to [0,1]: sigmoid of negated score
    iso_prob = 1.0 / (1.0 + np.exp(iso_score * 5))

    # Weighted ensemble: RF 40%, XGBoost 40%, Isolation 20%
    fraud_probability = 0.40 * rf_prob + 0.40 * xgb_prob + 0.20 * iso_prob
    fraud_probability = np.clip(fraud_probability, 0.0, 1.0)

    return {
        "fraud_probability": round(float(fraud_probability), 4),
        "rf_probability": round(rf_prob, 4),
        "xgb_probability": round(xgb_prob, 4),
        "iso_anomaly_score": round(iso_prob, 4),
        "features": features,
    }


def predict_all_fraud(businesses: list, models: dict) -> list:
    """
    Predict fraud probability for all businesses.

    Args:
        businesses: List of business dictionaries
        models: Trained fraud model dictionary

    Returns:
        Updated businesses list with fraud probabilities
    """
    print(f"[FraudDetect] Predicting fraud for {len(businesses)} businesses...")

    for biz in businesses:
        result = predict_fraud(biz, models)
        biz["fraud_probability"] = result["fraud_probability"]
        biz["_fraud_details"] = {
            "rf": result["rf_probability"],
            "xgb": result["xgb_probability"],
            "iso": result["iso_anomaly_score"],
        }

    probs = [b["fraud_probability"] for b in businesses]
    probs_arr = np.array(probs)
    print(f"[FraudDetect] Probability distribution: "
          f"min={probs_arr.min():.3f}, max={probs_arr.max():.3f}, "
          f"mean={probs_arr.mean():.3f}")

    return businesses
