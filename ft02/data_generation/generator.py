"""
Business Data Generator — Orchestrator

Generates complete synthetic business datasets by orchestrating all
sub-generators. Each business includes identity, loan history,
GST behavior, 36-month sales, purchases, and vendor-customer network.
"""

import numpy as np
from data_generation.business_identity import generate_business_identity
from data_generation.loan_history import generate_loan_history
from data_generation.gst_behavior import generate_gst_behavior
from data_generation.sales_timeseries import generate_sales_data
from data_generation.purchases_itc import generate_purchase_data
from data_generation.vendor_network import generate_network_data
from data_generation.fraud_injector import (
    assign_fraud_label,
    inject_fraud_indicators,
)


def generate_single_business(business_idx: int, total: int) -> dict:
    """
    Generate a complete synthetic business record.

    Args:
        business_idx: Index of this business in the batch
        total: Total businesses being generated

    Returns:
        Complete business dictionary with all sections
    """
    # Step 1: Determine fraud label
    is_fraud = assign_fraud_label(business_idx, total)

    # Step 2: Generate business identity
    identity = generate_business_identity(business_idx)

    sector = identity["sector"]
    business_age = identity["business_age"]
    sector_risk = identity["risk_sector_score"]

    # Step 3: Generate sales time series (needed for downstream)
    sales_data = generate_sales_data(sector, business_age, is_fraud)

    estimated_turnover = sales_data["estimated_turnover"]

    # Step 4: Generate purchase data (correlated with sales)
    purchase_data = generate_purchase_data(
        sales_data["monthly_sales"], is_fraud
    )

    # Step 5: Generate loan history
    loan_history = generate_loan_history(business_age, sector_risk, is_fraud)

    # Step 6: Generate GST behavior
    gst_behavior = generate_gst_behavior(business_age, estimated_turnover, is_fraud)

    # Step 7: Generate vendor-customer network
    network_data = generate_network_data(identity["gstin"], sector, is_fraud)

    # Step 8: Assemble business record
    business = {
        "business_identity": identity,
        "loan_history": loan_history,
        "gst_behavior": gst_behavior,
        "sales_data": sales_data,
        "purchase_data": purchase_data,
        "network_data": network_data,
        "fraud_label": int(is_fraud),
        # Placeholders — filled by scoring pipeline
        "credit_score": None,
        "fraud_probability": None,
        "explanations": [],
        "loan_decision": None,
    }

    # Step 9: Inject fraud indicators (analysis of existing data patterns)
    if is_fraud:
        fraud_info = inject_fraud_indicators(business)
        business["fraud_indicators"] = fraud_info
    else:
        business["fraud_indicators"] = {
            "fraud_indicators": [],
            "total_red_flags": 0,
            "max_severity": "none",
        }

    return business


def generate_business_dataset(n_businesses: int = 200,
                              seed: int = None) -> list:
    """
    Generate a complete synthetic business dataset.

    Args:
        n_businesses: Number of businesses to generate
        seed: Optional random seed for reproducibility

    Returns:
        List of complete business dictionaries
    """
    if seed is not None:
        np.random.seed(seed)

    businesses = []
    fraud_count = 0

    print(f"[Generator] Generating {n_businesses} synthetic businesses...")

    for i in range(n_businesses):
        business = generate_single_business(i, n_businesses)
        businesses.append(business)

        if business["fraud_label"] == 1:
            fraud_count += 1

        if (i + 1) % 50 == 0 or i == n_businesses - 1:
            print(f"  [{i + 1}/{n_businesses}] Generated "
                  f"(fraud: {fraud_count}/{i + 1} = "
                  f"{fraud_count / (i + 1) * 100:.1f}%)")

    print(f"[Generator] Complete. {fraud_count}/{n_businesses} fraudulent "
          f"({fraud_count / n_businesses * 100:.1f}%)")

    return businesses
