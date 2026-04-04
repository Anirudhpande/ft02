# MSME Risk Intelligence Platform

A behavior-driven risk intelligence system designed to analyze MSME (Micro, Small & Medium Enterprises) financial activity using alternative data signals. The platform enables fraud detection, continuous risk monitoring, explainable credit scoring, and adaptive decision-making for lending.

---

## Problem Statement

MSMEs face significant barriers in accessing credit due to the absence of formal credit history. Traditional credit evaluation systems rely heavily on static financial documents such as balance sheets and tax returns, which fail to reflect real-time business behavior.

Financial institutions also face challenges in:

* Detecting sophisticated fraud patterns such as circular transactions  
* Verifying the authenticity of reported turnover  
* Continuously monitoring business health after loan disbursement  
* Adapting to regulatory or policy changes dynamically  
* Identifying early warning signals of financial instability  

---

## Solution Overview

This project presents an MSME Risk Intelligence Platform that evaluates businesses using alternative behavioral financial signals such as GST filings, UPI transactions, and logistics activity.

Instead of relying on static documents, the system analyzes how a business behaves financially over time.

The platform:

* Generates an explainable, behavior-based credit score  
* Detects fraudulent transaction patterns, including circular money flow  
* Identifies mismatches between financial signals to detect fake turnover  
* Monitors risk continuously through behavioral changes  
* Adapts dynamically to regulatory changes without retraining  
* Provides interpretable insights for decision-making  

---

## System Pipeline


Business Activity
↓
Data Simulation / Collection
↓
Feature Engineering
↓
Behavioral Analysis
↓
Fraud Detection (Pattern + Graph-Based)
↓
Credit Scoring
↓
Explainability Layer
↓
Risk Monitoring
↓
Policy-Aware Adjustments
↓
Decision Support


---

## Core Components

### Data Simulation (`/simulate-data`)

Generates synthetic business activity to replicate real-world signals:

* GST filings representing tax compliance and revenue  
* UPI transactions representing cash flow and financial movement  
* Shipment data representing operational activity  

---

### Feature Engineering (`/generate-features`)

Transforms raw data into behavioral indicators:

* GST filing consistency and delays  
* Transaction frequency and volume  
* Invoice velocity and turnover estimation  
* Shipment activity and operational consistency  
* Cash flow stability  

Additional derived signals:

* Input tax credits (purchase-side validation)  
* Vendor-customer interaction patterns  
* Filing discipline metrics  

---

### Fraud Detection (`/fraud-check`)

The system detects fraud using both rule-based and structural analysis.

#### 1. Mismatch Detection

Identifies inconsistencies such as:

* High transaction volume with low invoice activity  
* Sudden spikes in reported sales without supporting signals  
* Inflated turnover not backed by operational activity  

#### 2. Circular Transaction Detection (Graph-Based)

Transactions are modeled as a directed graph:

* Nodes represent businesses  
* Edges represent financial transactions  

The system detects:

* Circular transaction loops (A → B → C → A)  
* Dense clusters of businesses transacting among themselves  
* Artificial inflation of transaction velocity  

These patterns indicate potential fake sales and coordinated fraud behavior.

---

### Credit Scoring (`/predict-score`)

Estimates creditworthiness using behavioral signals.

Current implementation uses a rule-based scoring mechanism based on:

* GST compliance  
* Transaction activity  
* Revenue strength  
* Behavioral consistency  

The scoring logic is designed to transition into machine learning models.

Example formulation:


score = base_score + weighted_behavioral_signals


Future extension:

* Logistic regression or tree-based models  
* Probability-based scoring systems  

---

### Explainability (`/explain-score`)

Provides transparent reasoning behind the score:

* Identifies contributing factors  
* Highlights positive and negative signals  
* Ensures interpretability for lenders  

---

### Risk Monitoring (`/risk-monitor`)

Tracks business performance over time by comparing behavioral patterns.

Detects:

* Decline in activity levels  
* Increase in filing delays  
* Revenue instability  
* Emerging risk signals  

Enables continuous monitoring rather than one-time evaluation.

---

### Policy-Aware Adjustment Layer

The system dynamically adapts to regulatory changes without retraining.

Example:

* During GST amnesty periods, filing delays are not penalized  
* Feature weights are adjusted dynamically  

This ensures:

* Fair evaluation  
* Regulatory compliance  
* Real-world adaptability  

---

### Fraud Network Visualization

The system represents transaction data as a network graph:

* Businesses as nodes  
* Transactions as edges  

The dashboard can visualize:

* Fraud rings  
* Flow of funds between entities  
* Network topology of suspicious activity  

This enables loan officers to directly interpret fraud structures.

---

### Business Validation Signals

The system incorporates additional validation factors:

* Basic business identity  
* Previous loan history  
* Turnover estimation  
* Input tax credits (purchase behavior)  
* Filing discipline  

---

### Additional Risk Indicators

The system evaluates broader risk signals:

* GST cancellation history  
* Multiple GST registrations  
* Sudden spikes in sales activity  
* Industry classification and sector-based risk  

---

## Example Output


GSTIN: 27ABCDE1234F1Z5
Credit Score: 742
Risk Band: Low
Fraud Flag: Possible
Fraud Type: Circular Transaction Pattern

Recommended Loan: 420000

Alerts:

Transaction activity does not match invoice data
Circular money flow detected

Key Factors:

Consistent GST filing
High transaction volume
Network-based anomaly detected

---

## Project Structure


backend/
├── api/
├── services/
├── utils/

dashboard/
data/
docs/


---

## Key Contributions

* Behavior-based credit evaluation using alternative financial signals  
* Graph-based fraud detection for circular transaction identification  
* Cross-verification of multiple signals to detect fake turnover  
* Explainable scoring system for transparency  
* Continuous risk monitoring instead of static evaluation  
* Policy-aware adaptive scoring mechanism  

---

## Future Scope

* Machine learning-based credit scoring models  
* Automated graph analytics for fraud detection  
* Real-time monitoring and alert systems  
* Bankruptcy prediction models  
* Loan recommendation engine  
* Integration with real financial and GST data sources  

---

## Conclusion

This project extends traditional credit scoring into a comprehensive risk intelligence system.

By combining behavioral analysis, fraud detection, explainability, and adaptability, it provides a more reliable and scalable approach to MSME credit evaluation and lending decision support.
