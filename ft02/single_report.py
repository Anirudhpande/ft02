"""
Single Business Report Generator

Generate a credit risk report for a specific GSTIN.
Since this is a simulation platform (no real GST database),
it generates realistic synthetic data tied to the given GSTIN,
scores it using trained models, and produces a full PDF report.

Usage:
    python single_report.py --gstin 27ABCDE1234F1Z5
    python single_report.py --gstin 27ABCDE1234F1Z5 --sector "IT Services" --age 5
"""

import os
import sys
import time
import argparse
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a credit risk report for a specific GSTIN"
    )
    parser.add_argument(
        "--gstin", type=str, required=True,
        help="15-character GSTIN (e.g., 27ABCDE1234F1Z5)"
    )
    parser.add_argument(
        "--sector", type=str, default=None,
        help="Business sector (e.g., 'IT Services', 'Manufacturing'). Random if not set."
    )
    parser.add_argument(
        "--age", type=int, default=None,
        help="Business age in years. Random if not set."
    )
    parser.add_argument(
        "--name", type=str, default=None,
        help="Business name. Auto-generated if not set."
    )
    parser.add_argument(
        "--constitution", type=str, default=None,
        choices=["Proprietorship", "Partnership", "Private Limited", "LLP"],
        help="Business constitution type."
    )
    parser.add_argument(
        "--fraud", action="store_true", default=False,
        help="Simulate as a fraudulent business (for testing)."
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--training-size", type=int, default=100,
        help="Number of synthetic businesses to train models on (default: 100)."
    )
    args = parser.parse_args()

    start_time = time.time()

    # Validate GSTIN format
    from utils.gst_validator import validate_gstin
    if not validate_gstin(args.gstin):
        print(f"[ERROR] Invalid GSTIN format: '{args.gstin}'")
        print("        Expected: 15 characters — 2-digit state code + 10-char PAN + entity + Z + check")
        print("        Example:  27ABCDE1234F1Z5")
        sys.exit(1)

    if args.seed is not None:
        np.random.seed(args.seed)

    print("=" * 60)
    print("  Single Business Credit Risk Report")
    print("=" * 60)
    print(f"  GSTIN: {args.gstin}")
    print("=" * 60)
    print()

    # ── Setup output directories ────────────────────────────────────────
    from utils.json_storage import ensure_output_dirs
    data_dir, reports_dir, charts_dir = ensure_output_dirs(PROJECT_ROOT)

    # ════════════════════════════════════════════════════════════════════
    # STEP 1: Generate training dataset (background businesses)
    # ════════════════════════════════════════════════════════════════════
    print("STEP 1: Training ML models on synthetic dataset...")
    from data_generation.generator import generate_business_dataset
    from credit_scoring.feature_builder import build_credit_features
    from fraud_detection.fraud_features import build_fraud_features

    training_businesses = generate_business_dataset(
        n_businesses=args.training_size, seed=args.seed or 42
    )

    for biz in training_businesses:
        biz["_credit_features"] = build_credit_features(biz)
        biz["_fraud_features"] = build_fraud_features(biz)

    # Train credit model
    from credit_scoring.model_trainer import train_credit_model
    credit_models = train_credit_model(training_businesses)

    # Score training businesses (needed before fraud model)
    from credit_scoring.scorer import score_all_businesses
    training_businesses = score_all_businesses(training_businesses, credit_models)

    # Train fraud model
    from fraud_detection.fraud_model import train_fraud_model
    fraud_models = train_fraud_model(training_businesses)

    print(f"[Models] Trained on {args.training_size} synthetic businesses\n")

    # ════════════════════════════════════════════════════════════════════
    # STEP 2: Generate target business with the given GSTIN
    # ════════════════════════════════════════════════════════════════════
    print("STEP 2: Generating business profile for target GSTIN...")
    target = _generate_target_business(args)

    print(f"  Business: {target['business_identity']['legal_name']}")
    print(f"  Sector:   {target['business_identity']['sector']}")
    print(f"  Age:      {target['business_identity']['business_age']} years")
    print(f"  Fraud:    {'Yes (simulated)' if target['fraud_label'] else 'No'}")
    print()

    # ════════════════════════════════════════════════════════════════════
    # STEP 3: Score the target business
    # ════════════════════════════════════════════════════════════════════
    print("STEP 3: Scoring target business...")

    # Credit features & score
    target["_credit_features"] = build_credit_features(target)
    target["_fraud_features"] = build_fraud_features(target)

    from credit_scoring.scorer import score_business
    credit_result = score_business(target, credit_models)
    target["credit_score"] = credit_result["credit_score"]
    target["_credit_features"] = credit_result["features"]

    # Fraud probability
    from fraud_detection.fraud_model import predict_fraud
    fraud_result = predict_fraud(target, fraud_models)
    target["fraud_probability"] = fraud_result["fraud_probability"]

    print(f"  Credit Score:      {target['credit_score']} / 900")
    print(f"  Fraud Probability: {target['fraud_probability']:.1%}")
    print()

    # ════════════════════════════════════════════════════════════════════
    # STEP 4: Generate explanations
    # ════════════════════════════════════════════════════════════════════
    print("STEP 4: Generating SHAP explanations...")
    from explainability.shap_explainer import explain_credit_score, explain_fraud_prediction
    from explainability.narrative_generator import compile_all_explanations

    credit_shap = explain_credit_score(target, credit_models)
    fraud_shap = explain_fraud_prediction(target, fraud_models)
    target["explanations"] = compile_all_explanations(target, credit_shap, fraud_shap)

    # ════════════════════════════════════════════════════════════════════
    # STEP 5: Bank decision
    # ════════════════════════════════════════════════════════════════════
    print("STEP 5: Running bank decision simulator...")
    from utils.decision_engine import make_loan_decision, format_decision_summary

    features_for_decision = target.get("_credit_features", {})
    features_for_decision.update({
        "estimated_turnover": target.get("sales_data", {}).get("estimated_turnover", 0),
        "dependency_on_single_customer": target.get("network_data", {}).get(
            "dependency_on_single_customer", 0.5
        ),
        "sales_volatility": target.get("sales_data", {}).get("sales_volatility", 0.3),
        "gst_cancellation_history": target.get("gst_behavior", {}).get(
            "gst_cancellation_history", False
        ),
    })
    decision = make_loan_decision(
        target["credit_score"],
        target["fraud_probability"],
        features_for_decision,
    )
    target["loan_decision"] = decision
    print()
    print(format_decision_summary(decision, target["business_identity"]["legal_name"]))
    print()

    # ════════════════════════════════════════════════════════════════════
    # STEP 6: Generate visualizations
    # ════════════════════════════════════════════════════════════════════
    print("STEP 6: Generating visualizations...")
    from visualizations.sales_chart import generate_sales_chart
    from visualizations.credit_gauge import generate_credit_gauge
    from visualizations.fraud_network import generate_fraud_network
    from visualizations.risk_radar import generate_risk_radar
    from visualizations.turnover_chart import generate_turnover_chart

    generate_sales_chart(target, charts_dir)
    generate_credit_gauge(target, charts_dir)
    generate_risk_radar(target, charts_dir)
    generate_turnover_chart(target, charts_dir)
    generate_fraud_network(target, charts_dir)
    print(f"  Charts saved to: {charts_dir}")

    # ════════════════════════════════════════════════════════════════════
    # STEP 7: Generate PDF report
    # ════════════════════════════════════════════════════════════════════
    print("STEP 7: Generating PDF report...")
    from report_generation.pdf_report import generate_pdf_report

    pdf_path = generate_pdf_report(target, charts_dir, reports_dir)
    print(f"  PDF saved to: {pdf_path}")

    # ════════════════════════════════════════════════════════════════════
    # STEP 8: Save business data to JSON
    # ════════════════════════════════════════════════════════════════════
    from utils.json_storage import save_single_business

    # Clean internal fields
    clean_target = {k: v for k, v in target.items() if not k.startswith("_")}
    save_single_business(clean_target, os.path.join(data_dir, "individual"))

    elapsed = time.time() - start_time
    print()
    print("=" * 60)
    print("  REPORT COMPLETE")
    print("=" * 60)
    print(f"  GSTIN:           {args.gstin}")
    print(f"  Business:        {target['business_identity']['legal_name']}")
    print(f"  Credit Score:    {target['credit_score']}")
    print(f"  Fraud Prob:      {target['fraud_probability']:.1%}")
    print(f"  Decision:        {decision['decision']}")
    print(f"  Loan Amount:     Rs.{decision['recommended_loan_amount']:,}")
    print(f"  Time:            {elapsed:.1f}s")
    print(f"  PDF:             {pdf_path}")
    print("=" * 60)


def _generate_target_business(args) -> dict:
    """Generate a synthetic business record for the given GSTIN."""
    from utils.constants import (
        SECTORS, SECTOR_NAMES, SECTOR_WEIGHTS,
        CONSTITUTIONS, CONSTITUTION_WEIGHTS,
        BUSINESS_LOCATIONS,
    )
    from data_generation.business_identity import generate_business_name
    from data_generation.sales_timeseries import generate_sales_data
    from data_generation.purchases_itc import generate_purchase_data
    from data_generation.loan_history import generate_loan_history
    from data_generation.gst_behavior import generate_gst_behavior
    from data_generation.vendor_network import generate_network_data
    from data_generation.fraud_injector import inject_fraud_indicators
    from synthetic_models.gmm_engine import create_age_sampler
    from utils.constants import BUSINESS_AGE_PARAMS
    from utils.gst_validator import extract_state_from_gstin
    from datetime import datetime, timedelta
    import random

    gstin = args.gstin
    is_fraud = args.fraud

    # Sector
    if args.sector and args.sector in SECTORS:
        sector = args.sector
    else:
        sector = np.random.choice(SECTOR_NAMES, p=SECTOR_WEIGHTS)

    sector_info = SECTORS[sector]
    risk_sector_score = sector_info["risk_score"]

    # Constitution
    if args.constitution:
        constitution = args.constitution
    else:
        constitution = np.random.choice(CONSTITUTIONS, p=CONSTITUTION_WEIGHTS)

    # Business age
    if args.age:
        business_age = args.age
    else:
        sampler = create_age_sampler(BUSINESS_AGE_PARAMS)
        business_age = max(1, int(round(sampler.sample_one())))

    # Location from GSTIN state code
    state_code = extract_state_from_gstin(gstin)
    location = None
    for loc in BUSINESS_LOCATIONS:
        if loc["state_code"] == state_code:
            location = loc
            break
    if not location:
        location = random.choice(BUSINESS_LOCATIONS)

    # PAN from GSTIN
    pan = gstin[2:12]

    # Business name
    if args.name:
        legal_name = args.name
        trade_name = args.name
    else:
        legal_name, trade_name = generate_business_name(sector)

    # Registration date
    today = datetime.now()
    reg_date = today - timedelta(days=business_age * 365 + random.randint(-180, 180))
    registration_date = reg_date.strftime("%Y-%m-%d")

    identity = {
        "gstin": gstin,
        "pan": pan,
        "legal_name": legal_name,
        "trade_name": trade_name,
        "business_constitution": constitution,
        "registration_date": registration_date,
        "business_age": business_age,
        "sector": sector,
        "business_location": f"{location['city']}, {location['state']}",
        "risk_sector_score": risk_sector_score,
    }

    # Generate remaining data
    sales_data = generate_sales_data(sector, business_age, is_fraud)
    purchase_data = generate_purchase_data(sales_data["monthly_sales"], is_fraud)
    loan_history = generate_loan_history(business_age, risk_sector_score, is_fraud)
    gst_behavior = generate_gst_behavior(
        business_age, sales_data["estimated_turnover"], is_fraud
    )
    network_data = generate_network_data(gstin, sector, is_fraud)

    business = {
        "business_identity": identity,
        "loan_history": loan_history,
        "gst_behavior": gst_behavior,
        "sales_data": sales_data,
        "purchase_data": purchase_data,
        "network_data": network_data,
        "fraud_label": int(is_fraud),
        "credit_score": None,
        "fraud_probability": None,
        "explanations": [],
        "loan_decision": None,
    }

    if is_fraud:
        business["fraud_indicators"] = inject_fraud_indicators(business)
    else:
        business["fraud_indicators"] = {
            "fraud_indicators": [],
            "total_red_flags": 0,
            "max_severity": "none",
        }

    return business


if __name__ == "__main__":
    main()
