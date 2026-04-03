"""
Purchases and Input Tax Credit Generator

Generates realistic purchase behavior correlated with sales data
using copula-based correlation modeling. Computes ITC claims
and purchase-to-sales ratios.
"""

import numpy as np
from synthetic_models.correlation_engine import generate_correlated_purchases


def generate_purchase_data(monthly_sales: list,
                           is_fraud: bool = False) -> dict:
    """
    Generate monthly purchase data correlated with sales.

    Args:
        monthly_sales: List of 36 monthly sales values
        is_fraud: Whether business is fraudulent

    Returns:
        Dict with monthly_purchases, input_tax_credit_claimed,
        and purchase_to_sales_ratio
    """
    # Generate correlated purchases
    monthly_purchases = generate_correlated_purchases(
        monthly_sales, is_fraud=is_fraud
    )

    # Round values
    monthly_purchases = [round(float(p), 2) for p in monthly_purchases]

    # Calculate Input Tax Credit (ITC) claimed
    # Standard GST rates: 5%, 12%, 18%, 28% — average ~15% for MSMEs
    gst_rate = np.random.choice([0.05, 0.12, 0.18, 0.28], p=[0.15, 0.30, 0.40, 0.15])

    if is_fraud:
        # Fraudulent businesses may over-claim ITC
        itc_inflation = np.random.uniform(1.2, 2.0)
        input_tax_credit = [round(p * gst_rate * itc_inflation, 2)
                            for p in monthly_purchases]
    else:
        input_tax_credit = [round(p * gst_rate, 2)
                            for p in monthly_purchases]

    # Purchase to sales ratio
    total_purchases = sum(monthly_purchases)
    total_sales = sum(monthly_sales)

    if total_sales > 0:
        purchase_to_sales_ratio = round(total_purchases / total_sales, 4)
    else:
        purchase_to_sales_ratio = 0.0

    return {
        "monthly_purchases": monthly_purchases,
        "input_tax_credit_claimed": input_tax_credit,
        "purchase_to_sales_ratio": purchase_to_sales_ratio,
    }
