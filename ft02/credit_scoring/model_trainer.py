"""
Credit Scoring Model Trainer

Trains XGBoost and LightGBM ensemble models for credit scoring.
Uses synthetic labels derived from a rule-based scoring function
for bootstrap training, then the trained model replaces the rules.
"""

import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score
from credit_scoring.feature_builder import get_feature_columns


def _generate_synthetic_labels(features_df: pd.DataFrame) -> np.ndarray:
    """
    Generate synthetic creditworthiness labels from a rule-based formula.
    Used to bootstrap the ML model training.

    Returns:
        Array of probabilities (0-1) representing creditworthiness
    """
    scores = np.zeros(len(features_df))

    # Positive signals
    scores += features_df["repayment_ratio"].values * 0.20
    scores += features_df["gst_compliance_score"].values * 0.15
    scores += features_df["turnover_stability"].values * 0.15
    scores += features_df["ps_consistency"].values * 0.10
    scores += features_df["vendor_diversification"].values * 0.08
    scores += features_df["customer_diversification"].values * 0.07
    scores += features_df["age_score"].values * 0.05

    # Negative signals
    scores -= features_df["sector_risk"].values * 0.08
    scores -= features_df["loan_burden_ratio"].clip(0, 2).values * 0.05
    scores -= (features_df["loan_defaults"].values / 5) * 0.07

    # Add noise to prevent perfect separation
    noise = np.random.normal(0, 0.05, len(scores))
    scores += noise

    # Clip to [0.05, 0.95]
    scores = np.clip(scores, 0.05, 0.95)

    return scores


def train_credit_model(businesses: list) -> dict:
    """
    Train credit scoring models on business dataset.

    Args:
        businesses: List of business dicts with extracted features

    Returns:
        Dict with 'xgb_model', 'lgbm_model', 'feature_columns', and metrics
    """
    from xgboost import XGBRegressor

    try:
        from lightgbm import LGBMRegressor
        has_lgbm = True
    except ImportError:
        has_lgbm = False
        print("[CreditModel] LightGBM not available, using XGBoost only")

    feature_cols = get_feature_columns()

    # Build feature matrix as DataFrame (preserves column names for LightGBM)
    features_list = []
    for biz in businesses:
        f = biz.get("_credit_features", {})
        features_list.append(f)

    df = pd.DataFrame(features_list)

    # Ensure all columns exist
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0.0

    X_df = df[feature_cols].fillna(0)
    X = X_df.values
    y = _generate_synthetic_labels(X_df)

    # ── Train XGBoost ───────────────────────────────────────────────────────
    xgb_model = XGBRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
    )
    xgb_model.fit(X, y)

    # Cross-validation score (suppress sklearn fit warnings for small datasets)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        n_cv = min(5, max(2, len(businesses) // 5))
        xgb_cv = cross_val_score(xgb_model, X, y, cv=n_cv, scoring="r2")
    print(f"[CreditModel] XGBoost CV R²: {np.mean(xgb_cv):.4f} ± {np.std(xgb_cv):.4f}")

    result = {
        "xgb_model": xgb_model,
        "lgbm_model": None,
        "feature_columns": feature_cols,
        "xgb_cv_r2": float(np.mean(xgb_cv)),
    }

    # ── Train LightGBM (if available) ───────────────────────────────────────
    if has_lgbm:
        lgbm_model = LGBMRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            verbose=-1,
        )
        lgbm_model.fit(X_df, y)  # Fit with DataFrame to preserve feature names

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lgbm_cv = cross_val_score(lgbm_model, X_df, y, cv=n_cv, scoring="r2")
        print(f"[CreditModel] LightGBM CV R²: {np.mean(lgbm_cv):.4f} ± {np.std(lgbm_cv):.4f}")

        result["lgbm_model"] = lgbm_model
        result["lgbm_cv_r2"] = float(np.mean(lgbm_cv))

    return result
