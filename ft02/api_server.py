"""
FinRisk-Lab — API Server

FastAPI backend that serves the credit risk analysis platform.
Models are pre-trained on startup for fast per-GSTIN analysis.

Usage:
    python api_server.py
    # or: uvicorn api_server:app --reload --port 8000
"""

import os
import sys
import time
import json
import traceback
import numpy as np

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── FastAPI App ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="FinRisk-Lab",
    description="AI-powered MSME credit risk analysis with fraud ring detection and GST amnesty overrides",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global model cache ──────────────────────────────────────────────────────────
_models = {
    "credit_models": None,
    "fraud_models": None,
    "ready": False,
    "training_time": 0,
}

# ── Output directories ─────────────────────────────────────────────────────────
OUTPUT_BASE = os.path.join(PROJECT_ROOT, "output")
DATA_DIR = os.path.join(OUTPUT_BASE, "data")
REPORTS_DIR = os.path.join(OUTPUT_BASE, "reports")
CHARTS_DIR = os.path.join(OUTPUT_BASE, "charts")


# ── Request / Response Models ───────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    gstin: str = Field(..., description="15-character GSTIN", min_length=15, max_length=15)
    business_name: Optional[str] = Field(None, description="Business name (auto-generated if empty)")
    sector: Optional[str] = Field(None, description="Business sector")
    business_age: Optional[int] = Field(None, ge=1, le=50, description="Business age in years")
    constitution: Optional[str] = Field(None, description="Business constitution type")
    simulate_fraud: bool = Field(False, description="Simulate as fraudulent (testing)")


class AnalyzeResponse(BaseModel):
    success: bool
    gstin: str
    business_name: str
    trade_name: str
    sector: str
    constitution: str
    business_age: int
    location: str
    registration_date: str
    risk_sector_score: int
    credit_score: int
    credit_probability: float
    risk_band: str
    fraud_probability: float
    fraud_risk_level: str
    decision: str
    recommended_loan_amount: int
    decision_confidence: float
    decision_reasons: list
    explanations: list
    fraud_indicators: list
    loan_history: dict
    gst_behavior: dict
    sales_summary: dict
    network_summary: dict
    purchase_summary: dict
    charts: dict
    pdf_url: str
    circular_trades_detail: list
    amnesty_status: dict
    elapsed_seconds: float
    bankruptcy_probability: float


# ── Startup: Pre-train models ──────────────────────────────────────────────────
@app.on_event("startup")
async def startup_train_models():
    """Pre-train ML models on synthetic data at server startup."""
    import warnings
    warnings.filterwarnings("ignore")

    print("\n" + "=" * 60)
    print("  FinRisk-Lab — Starting Up")
    print("=" * 60)
    print("[Startup] Pre-training ML models...")

    start = time.time()

    from utils.json_storage import ensure_output_dirs
    ensure_output_dirs(PROJECT_ROOT)

    from data_generation.generator import generate_business_dataset
    from credit_scoring.feature_builder import build_credit_features
    from fraud_detection.fraud_features import build_fraud_features
    from credit_scoring.model_trainer import train_credit_model
    from credit_scoring.scorer import score_all_businesses
    from fraud_detection.fraud_model import train_fraud_model

    np.random.seed(42)
    businesses = generate_business_dataset(n_businesses=200, seed=42)

    for biz in businesses:
        biz["_credit_features"] = build_credit_features(biz)
        biz["_fraud_features"] = build_fraud_features(biz)

    credit_models = train_credit_model(businesses)
    businesses = score_all_businesses(businesses, credit_models)
    fraud_models = train_fraud_model(businesses)

    _models["credit_models"] = credit_models
    _models["fraud_models"] = fraud_models
    _models["ready"] = True
    _models["training_time"] = time.time() - start

    print(f"[Startup] Models ready in {_models['training_time']:.1f}s")
    print(f"[Startup] Server is ready to accept requests")
    print("=" * 60 + "\n")


# ── API Routes ──────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    from utils.amnesty_config import get_active_amnesty_windows
    return {
        "status": "ready" if _models["ready"] else "training",
        "models_trained": _models["ready"],
        "training_time": round(_models["training_time"], 1),
        "amnesty_active": len(get_active_amnesty_windows()) > 0,
        "amnesty_windows": get_active_amnesty_windows(),
    }


@app.get("/api/sectors")
async def list_sectors():
    from utils.constants import SECTORS
    sectors = []
    for name, info in SECTORS.items():
        sectors.append({
            "name": name,
            "risk_score": info["risk_score"],
            "turnover_range": info["typical_turnover_range"],
        })
    return {"sectors": sectors}


# ── Amnesty Management Endpoints ───────────────────────────────────────────────

class AmnestyRequest(BaseModel):
    quarter: str = Field(..., description="Amnesty quarter label, e.g. Q4-2025")
    start_date: str = Field(..., description="Start date ISO format, e.g. 2025-10-01")
    end_date: str = Field(..., description="End date ISO format, e.g. 2025-12-31")
    description: Optional[str] = Field(None, description="Amnesty description")


@app.get("/api/amnesty")
async def list_amnesty_windows():
    """List all registered amnesty windows."""
    from utils.amnesty_config import get_all_amnesty_windows, is_any_amnesty_active
    return {
        "amnesty_active": is_any_amnesty_active(),
        "windows": get_all_amnesty_windows(),
    }


@app.post("/api/amnesty")
async def register_amnesty(request: AmnestyRequest):
    """
    Register a new GST amnesty quarter.
    Late filings during this window will NOT be penalised in
    credit scoring or fraud detection — without retraining the models.
    """
    from utils.amnesty_config import register_amnesty_window, is_any_amnesty_active
    record = register_amnesty_window(
        quarter=request.quarter,
        start_date=request.start_date,
        end_date=request.end_date,
        description=request.description or "",
    )
    return {
        "success": True,
        "message": f"Amnesty window '{request.quarter}' registered. "
                   f"Late-filing penalties are now suppressed.",
        "amnesty_active": is_any_amnesty_active(),
        "record": record,
    }


@app.delete("/api/amnesty/{quarter}")
async def deactivate_amnesty(quarter: str):
    """Deactivate an amnesty window so penalties resume."""
    from utils.amnesty_config import deactivate_amnesty_window, is_any_amnesty_active
    ok = deactivate_amnesty_window(quarter)
    if not ok:
        raise HTTPException(404, f"Amnesty window '{quarter}' not found")
    return {
        "success": True,
        "message": f"Amnesty window '{quarter}' deactivated. Penalties restored.",
        "amnesty_active": is_any_amnesty_active(),
    }


@app.put("/api/amnesty/{quarter}/activate")
async def reactivate_amnesty(quarter: str):
    """Re-activate a previously deactivated amnesty window."""
    from utils.amnesty_config import activate_amnesty_window, is_any_amnesty_active
    ok = activate_amnesty_window(quarter)
    if not ok:
        raise HTTPException(404, f"Amnesty window '{quarter}' not found")
    return {
        "success": True,
        "message": f"Amnesty window '{quarter}' re-activated.",
        "amnesty_active": is_any_amnesty_active(),
    }


# ── Twist 2: Optional Amnesty Scoring Endpoint ───────────────────────────────────

class ScoreRequest(BaseModel):
    gstin: str
    amnesty_quarter: Optional[str] = None
    amnesty_start: Optional[str] = None
    amnesty_end: Optional[str] = None
    adjustment_strategy: str = Field("feature_level", description="either 'feature_level' or 'score_level'")

@app.post("/api/score")
async def score_business_endpoint(request: ScoreRequest):
    """
    Direct model scoring allowing for dynamic amnesty adjustment override.
    Demonstrates adaptation to regulatory changes without retraining.
    """
    if not _models["ready"]:
        raise HTTPException(503, "Models are still training. Please wait.")
        
    start_time = time.time()
    from datetime import datetime
    
    # 1. Mock or build the target business record dynamically
    target = _build_target_business(AnalyzeRequest(gstin=request.gstin))
    
    # Check if this specific request declares an active amnesty
    amnesty_applied = False
    if request.amnesty_quarter and request.amnesty_start and request.amnesty_end:
        target["_amnesty_active_override"] = True
        amnesty_applied = True
        
    # 2. Score business with approach approach A (feature) or B (score)
    from credit_scoring.scorer import score_business, classify_risk_band
    strategy = request.adjustment_strategy if amnesty_applied else "feature_level"
    
    credit_result = score_business(target, _models["credit_models"], adjustment_strategy=strategy)
    target["credit_score"] = credit_result["credit_score"]
    target["_credit_features"] = credit_result["features"]
    
    # 3. Handle SHAP directly
    from explainability.shap_explainer import explain_credit_score
    credit_shap = explain_credit_score(target, _models["credit_models"])
    
    # Build a raw explanation text
    explanation_text = "Standard ML model penalty evaluation."
    if amnesty_applied:
        if strategy == "feature_level":
            explanation_text = f"Amnesty applied at Feature-Layer: Late filing history zeroes out for {request.amnesty_quarter} before model evaluation."
        else:
            explanation_text = f"Amnesty applied at Score-Layer: Post-prediction score calibration bumped base credit score upwards."
            
    return {
        "credit_score": target["credit_score"],
        "risk_band": classify_risk_band(target["credit_score"]),
        "adjusted_features": {
            "late_filings_count": target["_credit_features"].get("late_filings_count"),
            "months_not_filed": target["_credit_features"].get("months_not_filed"),
            "amnesty_applied": 1 if amnesty_applied else 0
        },
        "explanation": explanation_text,
        "timestamp": datetime.now().isoformat() + "Z",
        "elapsed_seconds": round(time.time() - start_time, 3)
    }

# ── Twist 1: Advanced Fraud Ring Check ─────────────────────────────────────────

class Transaction(BaseModel):
    sender: str
    receiver: str
    amount: float
    timestamp: str

class FraudCheckRequest(BaseModel):
    transactions: List[Transaction]

@app.post("/api/fraud-check")
async def check_fraud_rings(request: FraudCheckRequest):
    """
    Advanced standalone endpoint to identify circular money rotation.
    Takes raw UPI transactions with timestamps and exact amounts.
    Returns PyVis HTML URL and complete cyclic insights.
    """
    from fraud_detection.network_analyzer import analyze_transaction_network, generate_interactive_pyvis
    import time, os
    
    tx_dicts = [tx.model_dump() for tx in request.transactions]
    analysis = analyze_transaction_network(tx_dicts, time_window_hours=48)
    
    html_file = f"fraud_graph_{int(time.time())}.html"
    static_folder = os.path.join(PROJECT_ROOT, "static")
    output_path = os.path.join(static_folder, html_file)
    
    # Generate PyVis chart
    generate_interactive_pyvis(analysis["graph"], analysis["detected_cycles"], output_path)
    
    return {
        "fraud_flag": analysis["fraud_flag"],
        "fraud_score": analysis["fraud_score"],
        "fraud_type": analysis["fraud_type"],
        "involved_entities": analysis["involved_entities"],
        "detected_cycles": analysis["detected_cycles"],
        "visualization_url": f"/static/{html_file}"
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_gstin(request: AnalyzeRequest):
    """Analyze a GSTIN and generate a full credit risk report."""
    if not _models["ready"]:
        raise HTTPException(503, "Models are still training. Please wait.")

    start = time.time()

    try:
        result = _run_analysis(request)
        result["elapsed_seconds"] = round(time.time() - start, 2)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@app.get("/api/report/{gstin}/pdf")
async def download_pdf(gstin: str):
    """Download the PDF report for a GSTIN."""
    filepath = os.path.join(REPORTS_DIR, f"report_{gstin}.pdf")
    if not os.path.exists(filepath):
        raise HTTPException(404, f"Report not found for GSTIN: {gstin}")
    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=f"credit_report_{gstin}.pdf",
    )


@app.get("/api/chart/{filename}")
async def get_chart(filename: str):
    """Serve a chart image."""
    filepath = os.path.join(CHARTS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, f"Chart not found: {filename}")
    return FileResponse(filepath, media_type="image/png")


# ── Serve Frontend ──────────────────────────────────────────────────────────────
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# ── Analysis Logic ──────────────────────────────────────────────────────────────

def _run_analysis(request: AnalyzeRequest) -> dict:
    """Run the full credit risk analysis pipeline for a single GSTIN."""
    import warnings
    warnings.filterwarnings("ignore")

    from utils.gst_validator import validate_gstin
    if not validate_gstin(request.gstin):
        raise ValueError(f"Invalid GSTIN format: {request.gstin}")

    # Generate target business
    target = _build_target_business(request)

    # Detect fraud rings and close-loop money rotation dynamically
    from fraud_detection.network_analyzer import detect_fraud_rings
    network_data = target.get("network_data", {})
    edges_data = network_data.get("edges", [])
    if edges_data:
        detected_cycles = detect_fraud_rings(edges_data, request.gstin)
        target["network_data"]["circular_trades"] = detected_cycles
        
        # Mark edges as 'circular' if they are part of a detected cycle for visualizations
        cycle_edge_set = set()
        for cycle in detected_cycles:
            path = cycle.get("path", [])
            for i in range(len(path) - 1):
                cycle_edge_set.add((path[i], path[i+1]))
        
        for edge in target["network_data"]["edges"]:
            if (edge["source"], edge["target"]) in cycle_edge_set:
                edge["type"] = "circular"

    # Extract features
    from credit_scoring.feature_builder import build_credit_features
    from fraud_detection.fraud_features import build_fraud_features

    target["_credit_features"] = build_credit_features(target)
    target["_fraud_features"] = build_fraud_features(target)

    # Credit scoring
    from credit_scoring.scorer import score_business, classify_risk_band
    credit_result = score_business(target, _models["credit_models"])
    target["credit_score"] = credit_result["credit_score"]
    target["_credit_features"] = credit_result["features"]
    target["_credit_probability"] = credit_result["probability"]

    # Fraud detection
    from fraud_detection.fraud_model import predict_fraud
    fraud_result = predict_fraud(target, _models["fraud_models"])
    target["fraud_probability"] = fraud_result["fraud_probability"]

    # Explanations
    from explainability.shap_explainer import explain_credit_score, explain_fraud_prediction
    from explainability.narrative_generator import compile_all_explanations

    credit_shap = explain_credit_score(target, _models["credit_models"])
    fraud_shap = explain_fraud_prediction(target, _models["fraud_models"])
    target["explanations"] = compile_all_explanations(target, credit_shap, fraud_shap)

    # Bank decision
    from utils.decision_engine import make_loan_decision
    features_for_decision = target.get("_credit_features", {})
    features_for_decision.update({
        "estimated_turnover": target.get("sales_data", {}).get("estimated_turnover", 0),
        "dependency_on_single_customer": target.get("network_data", {}).get("dependency_on_single_customer", 0.5),
        "sales_volatility": target.get("sales_data", {}).get("sales_volatility", 0.3),
        "gst_cancellation_history": target.get("gst_behavior", {}).get("gst_cancellation_history", False),
    })
    decision = make_loan_decision(target["credit_score"], target["fraud_probability"], features_for_decision)
    target["loan_decision"] = decision

    # Generate visualizations
    from visualizations.sales_chart import generate_sales_chart
    from visualizations.credit_gauge import generate_credit_gauge
    from visualizations.fraud_network import generate_fraud_network, generate_fraud_network_html
    from visualizations.risk_radar import generate_risk_radar
    from visualizations.turnover_chart import generate_turnover_chart

    generate_sales_chart(target, CHARTS_DIR)
    generate_credit_gauge(target, CHARTS_DIR)
    generate_risk_radar(target, CHARTS_DIR)
    generate_turnover_chart(target, CHARTS_DIR)
    generate_fraud_network(target, CHARTS_DIR)
    generate_fraud_network_html(target, STATIC_DIR)

    # Generate dedicated fraud ring topology chart
    from visualizations.fraud_ring_chart import generate_fraud_ring_chart, generate_fraud_ring_html
    fraud_ring_path = generate_fraud_ring_chart(target, CHARTS_DIR)
    fraud_ring_html = generate_fraud_ring_html(target, STATIC_DIR)

    from visualizations.plotly_charts import generate_interactive_charts
    interactive_charts = generate_interactive_charts(target)

    # Generate PDF
    from report_generation.pdf_report import generate_pdf_report
    generate_pdf_report(target, CHARTS_DIR, REPORTS_DIR)

    # Save JSON
    from utils.json_storage import save_single_business
    clean = {k: v for k, v in target.items() if not k.startswith("_")}
    save_single_business(clean, os.path.join(DATA_DIR, "individual"))

    # Build response
    identity = target["business_identity"]
    gstin = identity["gstin"]
    sales = target.get("sales_data", {})
    network = target.get("network_data", {})
    fraud_prob = target["fraud_probability"]

    fraud_risk = "HIGH" if fraud_prob >= 0.5 else ("MODERATE" if fraud_prob >= 0.3 else "LOW")

    fraud_inds = target.get("fraud_indicators", {}).get("fraud_indicators", [])

    return {
        "success": True,
        "gstin": gstin,
        "business_name": identity["legal_name"],
        "trade_name": identity["trade_name"],
        "sector": identity["sector"],
        "constitution": identity["business_constitution"],
        "business_age": identity["business_age"],
        "location": identity["business_location"],
        "registration_date": identity["registration_date"],
        "risk_sector_score": identity["risk_sector_score"],
        "credit_score": target["credit_score"],
        "credit_probability": round(target.get("_credit_probability", 0), 4),
        "risk_band": classify_risk_band(target["credit_score"]),
        "fraud_probability": round(fraud_prob, 4),
        "fraud_risk_level": fraud_risk,
        "decision": decision["decision"],
        "recommended_loan_amount": decision["recommended_loan_amount"],
        "decision_confidence": round(decision["confidence"], 2),
        "decision_reasons": decision["reasons"],
        "explanations": target.get("explanations", []),
        "fraud_indicators": fraud_inds,
        "loan_history": target.get("loan_history", {}),
        "gst_behavior": target.get("gst_behavior", {}),
        "sales_summary": {
            "estimated_turnover": sales.get("estimated_turnover", 0),
            "sales_volatility": sales.get("sales_volatility", 0),
            "monthly_sales": sales.get("monthly_sales", []),
            "spike_count": len(sales.get("sudden_sales_spikes", [])),
        },
        "network_summary": {
            "vendor_count": network.get("vendor_count", 0),
            "customer_count": network.get("customer_count", 0),
            "concentration_ratio": network.get("customer_concentration_ratio", 0),
            "dependency_single_customer": network.get("dependency_on_single_customer", 0),
            "circular_trades": len(network.get("circular_trades", [])),
            "circular_trades_count": len(network.get("circular_trades", [])),
        },
        "circular_trades_detail": [
            {
                "path": ct.get("path", []),
                "rotated_funds": ct.get("rotated_funds", 0),
                "type": ct.get("type", "circular_trading"),
            }
            for ct in network.get("circular_trades", [])
        ],
        "purchase_summary": {
            "purchase_to_sales_ratio": target.get("purchase_data", {}).get("purchase_to_sales_ratio", 0),
        },
        "charts": interactive_charts,
        "pdf_url": f"/api/report/{gstin}/pdf",
        "amnesty_status": _build_amnesty_status(target),
        "elapsed_seconds": 0,
        "bankruptcy_probability": _compute_bankruptcy_probability(target),
    }

def _compute_bankruptcy_probability(target: dict) -> float:
    """Derive bankruptcy probability from credit features deterministically."""
    feats = target.get("_credit_features", {})
    score = target.get("credit_score", 500)
    fraud_prob = target.get("fraud_probability", 0.1)
    defaults = target.get("loan_history", {}).get("loan_defaults", 0)
    late = feats.get("late_filings_count", 0)
    volatility = target.get("sales_data", {}).get("sales_volatility", 0.3)

    # Higher score = lower bankruptcy risk
    base = max(0, (700 - score) / 700)
    bankruptcy_prob = (
        base * 0.5
        + fraud_prob * 0.25
        + min(defaults / 5, 1) * 0.15
        + min(late / 12, 1) * 0.05
        + volatility * 0.05
    )
    return round(min(max(bankruptcy_prob, 0.01), 0.98), 4)


# ── Trend Data Endpoint ─────────────────────────────────────────────────────────
@app.get("/api/trend/{gstin}")
async def get_risk_trend(gstin: str):
    """Return 12-month synthetic risk trend data for a given GSTIN."""
    import hashlib
    import random
    seed = int(hashlib.md5(gstin.encode()).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    base_score = rng.randint(420, 750)
    base_revenue = rng.randint(500000, 5000000)

    risk_scores, revenues, gst_delays, loan_health = [], [], [], []
    for i in range(12):
        drift = rng.uniform(-0.08, 0.10)
        base_score = max(300, min(900, int(base_score * (1 + drift))))
        risk_scores.append(base_score)

        rev_drift = rng.uniform(-0.12, 0.15)
        base_revenue = max(100000, int(base_revenue * (1 + rev_drift)))
        revenues.append(base_revenue)

        gst_delays.append(rng.randint(0, 4))
        loan_health.append(round(rng.uniform(0.5, 1.0), 2))

    # Detect rapid escalation: if risk dropped more than 20% over the year
    escalation = risk_scores[-1] < risk_scores[0] * 0.80
    drop_pct = round((risk_scores[0] - risk_scores[-1]) / risk_scores[0] * 100, 1)

    return {
        "gstin": gstin,
        "months": months,
        "risk_scores": risk_scores,
        "revenues": revenues,
        "gst_delays": gst_delays,
        "loan_health": loan_health,
        "escalation_alert": escalation,
        "escalation_message": (
            f"\u26a0\ufe0f Rapid Risk Escalation Detected — score dropped {drop_pct}% over 12 months"
            if escalation else None
        ),
    }


# ── Stress Test Endpoint ────────────────────────────────────────────────────────
class StressTestRequest(BaseModel):
    gstin: str
    revenue_drop_pct: float = Field(0, ge=0, le=100, description="Revenue drop percentage")
    loan_increase_pct: float = Field(0, ge=0, le=200, description="Loan obligation increase %")
    gst_delay_months: int = Field(0, ge=0, le=12, description="Additional GST delay months")
    industry_risk_delta: float = Field(0, ge=-3, le=3, description="Industry risk score delta")

@app.post("/api/stress-test")
async def run_stress_test(request: StressTestRequest):
    """Re-score business under stress scenario and return before/after comparison."""
    if not _models["ready"]:
        raise HTTPException(503, "Models are still training. Please wait.")

    from credit_scoring.feature_builder import build_credit_features
    from fraud_detection.fraud_features import build_fraud_features
    from credit_scoring.scorer import score_business, classify_risk_band
    from fraud_detection.fraud_model import predict_fraud

    # Build baseline business
    target = _build_target_business(AnalyzeRequest(gstin=request.gstin))
    target["_credit_features"] = build_credit_features(target)
    target["_fraud_features"] = build_fraud_features(target)
    before_credit = score_business(target, _models["credit_models"])
    before_fraud = predict_fraud(target, _models["fraud_models"])
    before_score = before_credit["credit_score"]
    before_fraud_p = round(before_fraud["fraud_probability"], 4)
    before_bankruptcy = _compute_bankruptcy_probability({**target, "credit_score": before_score, "fraud_probability": before_fraud_p})

    # Apply stress modifications
    import copy
    stressed = copy.deepcopy(target)
    sales = stressed.get("sales_data", {})
    if request.revenue_drop_pct > 0:
        factor = 1 - request.revenue_drop_pct / 100
        sales["estimated_turnover"] = sales.get("estimated_turnover", 1000000) * factor
        sales["monthly_sales"] = [s * factor for s in sales.get("monthly_sales", [])]
        sales["sales_volatility"] = min(1, sales.get("sales_volatility", 0.3) + request.revenue_drop_pct / 200)
    if request.gst_delay_months > 0:
        gst = stressed.get("gst_behavior", {})
        gst["late_filings_count"] = gst.get("late_filings_count", 0) + request.gst_delay_months
        gst["months_not_filed"] = gst.get("months_not_filed", 0) + max(0, request.gst_delay_months - 3)
    if request.loan_increase_pct > 0:
        loans = stressed.get("loan_history", {})
        loans["total_loan_amount"] = loans.get("total_loan_amount", 500000) * (1 + request.loan_increase_pct / 100)
    if request.industry_risk_delta != 0:
        identity = stressed.get("business_identity", {})
        identity["risk_sector_score"] = max(1, min(10, identity.get("risk_sector_score", 5) + request.industry_risk_delta))

    stressed["_credit_features"] = build_credit_features(stressed)
    stressed["_fraud_features"] = build_fraud_features(stressed)
    after_credit = score_business(stressed, _models["credit_models"])
    after_fraud = predict_fraud(stressed, _models["fraud_models"])
    after_score = after_credit["credit_score"]
    after_fraud_p = round(after_fraud["fraud_probability"], 4)
    after_bankruptcy = _compute_bankruptcy_probability({**stressed, "credit_score": after_score, "fraud_probability": after_fraud_p})

    return {
        "gstin": request.gstin,
        "scenario": {
            "revenue_drop_pct": request.revenue_drop_pct,
            "loan_increase_pct": request.loan_increase_pct,
            "gst_delay_months": request.gst_delay_months,
            "industry_risk_delta": request.industry_risk_delta,
        },
        "before": {
            "credit_score": before_score,
            "risk_band": classify_risk_band(before_score),
            "fraud_probability": before_fraud_p,
            "bankruptcy_probability": before_bankruptcy,
        },
        "after": {
            "credit_score": after_score,
            "risk_band": classify_risk_band(after_score),
            "fraud_probability": after_fraud_p,
            "bankruptcy_probability": after_bankruptcy,
        },
        "delta": {
            "credit_score": after_score - before_score,
            "fraud_probability": round(after_fraud_p - before_fraud_p, 4),
            "bankruptcy_probability": round(after_bankruptcy - before_bankruptcy, 4),
        },
    }


def _build_amnesty_status(target: dict) -> dict:
    """Build amnesty status metadata for the API response."""
    from utils.amnesty_config import is_any_amnesty_active, get_active_amnesty_windows

    amnesty_active = is_any_amnesty_active()
    active_windows = get_active_amnesty_windows()
    credit_features = target.get("_credit_features", {})

    raw_gst = target.get("gst_behavior", {})
    original_late = raw_gst.get("late_filings_count", 0)
    original_months = raw_gst.get("months_not_filed", 0)

    adjusted_fields = []
    if amnesty_active:
        if original_late > 0:
            adjusted_fields.append({
                "field": "late_filings_count",
                "original_value": original_late,
                "adjusted_value": 0,
                "reason": "Suppressed under GST amnesty scheme",
            })
        if original_months > 0:
            adjusted_fields.append({
                "field": "months_not_filed",
                "original_value": original_months,
                "adjusted_value": 0,
                "reason": "Suppressed under GST amnesty scheme",
            })
        if original_late > 0 or original_months > 0:
            adjusted_fields.append({
                "field": "gst_compliance_score",
                "original_value": "recalculated (penalties removed)",
                "adjusted_value": round(credit_features.get("gst_compliance_score", 0), 4),
                "reason": "Late-filing penalties excluded from compliance score",
            })
            adjusted_fields.append({
                "field": "filing_gap_score",
                "original_value": "recalculated (penalties removed)",
                "adjusted_value": 0.0,
                "reason": "Filing gap severity reset under amnesty",
            })

    return {
        "amnesty_active": amnesty_active,
        "active_windows": active_windows,
        "adjustments_applied": len(adjusted_fields),
        "adjusted_fields": adjusted_fields,
        "message": (
            f"GST Amnesty active — {len(adjusted_fields)} feature weights "
            f"dynamically adjusted without model retraining."
            if amnesty_active else "No amnesty scheme active."
        ),
    }


def _build_target_business(request: AnalyzeRequest) -> dict:
    """Generate synthetic business data for a given GSTIN."""
    import random
    from datetime import datetime, timedelta
    from utils.constants import (
        SECTORS, SECTOR_NAMES, SECTOR_WEIGHTS,
        CONSTITUTIONS, CONSTITUTION_WEIGHTS, BUSINESS_LOCATIONS,
        BUSINESS_AGE_PARAMS,
    )
    from data_generation.business_identity import generate_business_name
    from data_generation.sales_timeseries import generate_sales_data
    from data_generation.purchases_itc import generate_purchase_data
    from data_generation.loan_history import generate_loan_history
    from data_generation.gst_behavior import generate_gst_behavior
    from data_generation.vendor_network import generate_network_data
    from data_generation.fraud_injector import inject_fraud_indicators
    from synthetic_models.gmm_engine import create_age_sampler
    from utils.gst_validator import extract_state_from_gstin

    gstin = request.gstin
    is_fraud = request.simulate_fraud

    # Sector
    if request.sector and request.sector in SECTORS:
        sector = request.sector
    else:
        sector = np.random.choice(SECTOR_NAMES, p=SECTOR_WEIGHTS)

    sector_info = SECTORS[sector]

    # Constitution
    if request.constitution and request.constitution in CONSTITUTIONS:
        constitution = request.constitution
    else:
        constitution = np.random.choice(CONSTITUTIONS, p=CONSTITUTION_WEIGHTS)

    # Age
    if request.business_age:
        business_age = request.business_age
    else:
        sampler = create_age_sampler(BUSINESS_AGE_PARAMS)
        business_age = max(1, int(round(sampler.sample_one())))

    # Location
    state_code = extract_state_from_gstin(gstin)
    location = next((l for l in BUSINESS_LOCATIONS if l["state_code"] == state_code), random.choice(BUSINESS_LOCATIONS))

    pan = gstin[2:12]

    if request.business_name:
        legal_name = request.business_name
        trade_name = request.business_name
    else:
        legal_name, trade_name = generate_business_name(sector)

    reg_date = datetime.now() - timedelta(days=business_age * 365 + random.randint(-180, 180))

    identity = {
        "gstin": gstin,
        "pan": pan,
        "legal_name": legal_name,
        "trade_name": trade_name,
        "business_constitution": constitution,
        "registration_date": reg_date.strftime("%Y-%m-%d"),
        "business_age": business_age,
        "sector": sector,
        "business_location": f"{location['city']}, {location['state']}",
        "risk_sector_score": sector_info["risk_score"],
    }

    sales_data = generate_sales_data(sector, business_age, is_fraud)
    purchase_data = generate_purchase_data(sales_data["monthly_sales"], is_fraud)
    loan_history = generate_loan_history(business_age, sector_info["risk_score"], is_fraud)
    gst_behavior = generate_gst_behavior(business_age, sales_data["estimated_turnover"], is_fraud)
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
            "fraud_indicators": [], "total_red_flags": 0, "max_severity": "none",
        }

    return business


# ── Entry Point ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
