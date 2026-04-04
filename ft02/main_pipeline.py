"""
FinRisk-Lab — Main Pipeline

Entry point that orchestrates the complete simulation:
1. Generate synthetic businesses
2. Save to JSON
3. Train credit scoring model
4. Train fraud detection model
5. Score all businesses
6. Detect fraud probabilities
7. Generate SHAP explanations
8. Generate visualizations
9. Generate PDF reports
10. Run bank decision simulator
11. Print summary

Usage:
    python main_pipeline.py --count 200 --seed 42
"""

import os
import sys
import time
import argparse
import numpy as np

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    parser = argparse.ArgumentParser(
        description="FinRisk-Lab Simulation Platform"
    )
    parser.add_argument(
        "--count", type=int, default=200,
        help="Number of businesses to generate (default: 200)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--skip-reports", action="store_true",
        help="Skip PDF report generation (faster for testing)"
    )
    parser.add_argument(
        "--skip-charts", action="store_true",
        help="Skip chart generation (faster for testing)"
    )
    args = parser.parse_args()

    start_time = time.time()

    print("=" * 70)
    print("  FinRisk-Lab — Simulation Platform")
    print("=" * 70)
    print(f"  Businesses: {args.count}")
    print(f"  Seed: {args.seed}")
    print("=" * 70)
    print()

    # ── Setup output directories ────────────────────────────────────────────
    from utils.json_storage import ensure_output_dirs
    output_base = PROJECT_ROOT
    data_dir, reports_dir, charts_dir = ensure_output_dirs(output_base)
    print(f"[Setup] Output directories ready")

    # ════════════════════════════════════════════════════════════════════════
    # STEP 1: Generate Synthetic Businesses
    # ════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("STEP 1: Generating Synthetic Business Data")
    print("─" * 50)

    from data_generation.generator import generate_business_dataset
    businesses = generate_business_dataset(n_businesses=args.count, seed=args.seed)

    # ════════════════════════════════════════════════════════════════════════
    # STEP 2: Extract Credit Features
    # ════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("STEP 2: Extracting Credit & Fraud Features")
    print("─" * 50)

    from credit_scoring.feature_builder import build_credit_features
    from fraud_detection.fraud_features import build_fraud_features

    for biz in businesses:
        biz["_credit_features"] = build_credit_features(biz)
        biz["_fraud_features"] = build_fraud_features(biz)

    print(f"[Features] Extracted features for {len(businesses)} businesses")

    # ════════════════════════════════════════════════════════════════════════
    # STEP 3: Train Credit Scoring Model
    # ════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("STEP 3: Training Credit Scoring Model")
    print("─" * 50)

    from credit_scoring.model_trainer import train_credit_model
    credit_models = train_credit_model(businesses)

    # ════════════════════════════════════════════════════════════════════════
    # STEP 4: Score All Businesses
    # ════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("STEP 4: Scoring All Businesses")
    print("─" * 50)

    from credit_scoring.scorer import score_all_businesses
    businesses = score_all_businesses(businesses, credit_models)

    # ════════════════════════════════════════════════════════════════════════
    # STEP 5: Train Fraud Detection Model
    # ════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("STEP 5: Training Fraud Detection Model")
    print("─" * 50)

    from fraud_detection.fraud_model import train_fraud_model, predict_all_fraud
    fraud_models = train_fraud_model(businesses)

    # ════════════════════════════════════════════════════════════════════════
    # STEP 6: Predict Fraud Probabilities
    # ════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("STEP 6: Predicting Fraud Probabilities")
    print("─" * 50)

    businesses = predict_all_fraud(businesses, fraud_models)

    # ════════════════════════════════════════════════════════════════════════
    # STEP 7: Generate Explanations
    # ════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("STEP 7: Generating SHAP Explanations")
    print("─" * 50)

    from explainability.shap_explainer import explain_credit_score, explain_fraud_prediction
    from explainability.narrative_generator import compile_all_explanations

    for i, biz in enumerate(businesses):
        credit_shap = explain_credit_score(biz, credit_models)
        fraud_shap = explain_fraud_prediction(biz, fraud_models)
        biz["explanations"] = compile_all_explanations(biz, credit_shap, fraud_shap)

        if (i + 1) % 50 == 0:
            print(f"  [{i + 1}/{len(businesses)}] Explanations generated")

    print(f"[Explain] Generated explanations for {len(businesses)} businesses")

    # ════════════════════════════════════════════════════════════════════════
    # STEP 8: Bank Decision Simulator
    # ════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("STEP 8: Running Bank Decision Simulator")
    print("─" * 50)

    from utils.decision_engine import make_loan_decision

    decisions = {"APPROVE": 0, "REVIEW": 0, "REJECT": 0}
    for biz in businesses:
        features_for_decision = biz.get("_credit_features", {})
        features_for_decision.update({
            "estimated_turnover": biz.get("sales_data", {}).get("estimated_turnover", 0),
            "dependency_on_single_customer": biz.get("network_data", {}).get(
                "dependency_on_single_customer", 0.5
            ),
            "sales_volatility": biz.get("sales_data", {}).get("sales_volatility", 0.3),
            "gst_cancellation_history": biz.get("gst_behavior", {}).get(
                "gst_cancellation_history", False
            ),
        })
        decision = make_loan_decision(
            biz["credit_score"],
            biz["fraud_probability"],
            features_for_decision,
        )
        biz["loan_decision"] = decision
        decisions[decision["decision"]] += 1

    total = len(businesses)
    print(f"[Decision] Results: "
          f"APPROVE: {decisions['APPROVE']} ({decisions['APPROVE']/total:.0%}), "
          f"REVIEW: {decisions['REVIEW']} ({decisions['REVIEW']/total:.0%}), "
          f"REJECT: {decisions['REJECT']} ({decisions['REJECT']/total:.0%})")

    # ════════════════════════════════════════════════════════════════════════
    # STEP 9: Generate Visualizations
    # ════════════════════════════════════════════════════════════════════════
    if not args.skip_charts:
        print("\n" + "─" * 50)
        print("STEP 9: Generating Visualizations")
        print("─" * 50)

        from visualizations.sales_chart import generate_sales_chart
        from visualizations.credit_gauge import generate_credit_gauge
        from visualizations.fraud_network import generate_fraud_network
        from visualizations.risk_radar import generate_risk_radar
        from visualizations.turnover_chart import generate_turnover_chart

        for i, biz in enumerate(businesses):
            generate_sales_chart(biz, charts_dir)
            generate_credit_gauge(biz, charts_dir)
            generate_risk_radar(biz, charts_dir)
            generate_turnover_chart(biz, charts_dir)

            # Network chart only for first 50 (expensive)
            if i < 50 or biz.get("fraud_label") == 1:
                generate_fraud_network(biz, charts_dir)

            if (i + 1) % 50 == 0:
                print(f"  [{i + 1}/{len(businesses)}] Charts generated")

        print(f"[Charts] Generated visualizations for {len(businesses)} businesses")
    else:
        print("\n[Charts] Skipped (--skip-charts)")

    # ════════════════════════════════════════════════════════════════════════
    # STEP 10: Generate PDF Reports
    # ════════════════════════════════════════════════════════════════════════
    if not args.skip_reports:
        print("\n" + "─" * 50)
        print("STEP 10: Generating PDF Reports")
        print("─" * 50)

        from report_generation.pdf_report import generate_pdf_report

        for i, biz in enumerate(businesses):
            generate_pdf_report(biz, charts_dir, reports_dir)

            if (i + 1) % 50 == 0:
                print(f"  [{i + 1}/{len(businesses)}] Reports generated")

        print(f"[Reports] Generated {len(businesses)} PDF reports")
    else:
        print("\n[Reports] Skipped (--skip-reports)")

    # ════════════════════════════════════════════════════════════════════════
    # STEP 11: Save to JSON
    # ════════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("STEP 11: Saving Data to JSON")
    print("─" * 50)

    # Clean internal fields before saving
    for biz in businesses:
        for key in list(biz.keys()):
            if key.startswith("_"):
                del biz[key]

    from utils.json_storage import save_all_businesses
    json_path = os.path.join(data_dir, "business_data.json")
    save_all_businesses(businesses, json_path)

    # ════════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ════════════════════════════════════════════════════════════════════════
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETE")
    print("=" * 70)

    scores = [b["credit_score"] for b in businesses]
    frauds = [b["fraud_probability"] for b in businesses]
    fraud_labels = [b["fraud_label"] for b in businesses]

    print(f"  Total Businesses:    {len(businesses)}")
    print(f"  Fraudulent:          {sum(fraud_labels)} ({sum(fraud_labels)/len(businesses):.0%})")
    print(f"  Credit Score Range:  {min(scores)} - {max(scores)}")
    print(f"  Mean Credit Score:   {np.mean(scores):.0f}")
    print(f"  Mean Fraud Prob:     {np.mean(frauds):.3f}")
    print(f"  Decisions:           APPROVE({decisions['APPROVE']}) | "
          f"REVIEW({decisions['REVIEW']}) | REJECT({decisions['REJECT']})")
    print(f"  Elapsed Time:        {elapsed:.1f}s")
    print(f"\n  Output:")
    print(f"    Data:    {json_path}")
    print(f"    Charts:  {charts_dir}")
    print(f"    Reports: {reports_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
