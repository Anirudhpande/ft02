def calculate_credit_score(features):

    score = 600  # base score

    # 📊 GST behavior
    if features["avg_filing_delay"] <= 0:
        score += 50
    else:
        score -= 30

    # 💰 transaction strength
    if features["transaction_count"] > 150:
        score += 40
    else:
        score -= 20

    # 📈 stability
    if features["sales_variance"] < 500000000:
        score += 30
    else:
        score -= 30

    # 🚚 logistics activity
    if features["shipment_count"] > 10:
        score += 20

    # normalize
    score = max(300, min(score, 900))

    return score
def classify_risk(score):

    if score >= 750:
        return "LOW RISK"
    elif score >= 600:
        return "MEDIUM RISK"
    else:
        return "HIGH RISK"
    
def recommend_loan(score):

    if score >= 750:
        return 500000
    elif score >= 600:
        return 250000
    else:
        return 50000