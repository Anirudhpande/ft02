# MSME Risk Intelligence Platform

An AI-driven system designed to analyze MSME (Micro, Small & Medium Enterprises) financial behavior using alternative data signals to detect fraud, monitor risk, predict business failure, and recommend loans.

---

## Problem Statement

MSMEs often struggle to access credit due to the lack of formal financial history. Traditional credit scoring systems rely on static financial documents and fail to capture real-time business activity.

Financial institutions also face challenges in:

* Identifying fraudulent transaction behavior
* Monitoring businesses continuously after lending
* Detecting early signs of financial distress

---

## Solution Overview

This project presents a risk intelligence platform that evaluates businesses using alternative financial signals such as GST filings, UPI transactions, and logistics activity.

The system:

* Generates an explainable credit score
* Detects fraudulent transaction patterns
* Monitors changes in business activity over time
* Identifies early indicators of business failure
* Recommends appropriate loan amounts

---

## System Pipeline

```
Business Activity
      ↓
Data Simulation / Collection
      ↓
Feature Engineering
      ↓
Fraud Detection
      ↓
Credit Scoring
      ↓
Explainability
      ↓
Risk Monitoring
      ↓
Bankruptcy Prediction
      ↓
Loan Recommendation
```

---

## Core Components

### Data Simulation (`/simulate-data`)

Generates synthetic business activity to replicate real-world signals:

* GST filings representing tax compliance
* UPI transactions representing cash flow
* Shipment data representing operational activity

---

### Feature Engineering (`/generate-features`)

Transforms raw data into measurable indicators:

* GST consistency
* Transaction frequency
* Invoice velocity
* Shipment activity
* Cash flow stability

---

### Fraud Detection (`/fraud-check`)

Models transactions as a directed graph to identify suspicious patterns.

The system detects:

* Circular transaction loops
* Repeated low-margin trade cycles
* Closed groups of businesses transacting primarily among themselves

---

### Credit Scoring (`/predict-score`)

Estimates creditworthiness based on behavioral signals.

The score is computed as:

```
score = 300 + (probability × 600)
```

Factors considered include:

* Tax compliance
* Transaction behavior
* Business activity
* Fraud indicators

---

### Explainability (`/explain-score`)

Provides clear reasons for the generated score, ensuring transparency in decision-making.

---

### Risk Monitoring (`/risk-monitor`)

Tracks business performance over time by comparing current and historical signals.

The system identifies:

* Significant drops in credit score
* Declines in transaction activity
* Deterioration in compliance behavior

Alerts are generated when risk increases.

---

### Bankruptcy Prediction (`/bankruptcy`)

Identifies early warning signs of potential business failure based on declining activity and behavioral changes.

---

### Loan Recommendation (`/recommend-loan`)

Determines loan eligibility and amount based on credit score and overall business health.

Example logic:

* Higher scores correspond to higher loan multipliers
* Lower scores result in more conservative lending

---

## Example Output

```
GSTIN: 27ABCDE1234F1Z5
Credit Score: 742
Risk Band: Low
Fraud Flag: No
Bankruptcy Risk: Moderate

Recommended Loan: 420000

Alerts:
- Transaction volume decreased

Key Factors:
- Consistent GST filing
- Stable transaction activity
```

---

## Project Structure

```
backend/
  ├── api/
  ├── services/
  ├── models/
  ├── database/
  └── utils/

dashboard/
data/
docs/
```

---


## Key Contributions

* Use of alternative financial signals for credit evaluation
* Graph-based fraud detection approach
* Continuous risk monitoring instead of one-time scoring
* Early-stage bankruptcy prediction
* Explainable decision-making pipeline

---

## Future Scope

* Integration with real-world financial data sources
* Enhanced modeling for risk prediction
* Real-time monitoring capabilities
* Improved visualization of transaction networks

---

## Conclusion

This project extends traditional credit scoring into a broader risk intelligence system. By combining behavioral analysis, fraud detection, and continuous monitoring, it provides a more reliable and transparent approach to MSME credit evaluation.
