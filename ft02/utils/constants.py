"""
Constants and Configuration for MSME Credit Risk Platform

Contains sector definitions, distribution parameters, location data,
and business name components used across all generation modules.
"""

# ─── Sector Definitions with Risk Scores ───────────────────────────────────────
# Risk scores: 1 (lowest risk) to 10 (highest risk)
SECTORS = {
    "IT Services":          {"risk_score": 2, "typical_turnover_range": (500000, 5000000)},
    "Manufacturing":        {"risk_score": 4, "typical_turnover_range": (1000000, 10000000)},
    "Textile":              {"risk_score": 5, "typical_turnover_range": (800000, 8000000)},
    "Food Processing":      {"risk_score": 4, "typical_turnover_range": (600000, 6000000)},
    "Retail Trade":         {"risk_score": 3, "typical_turnover_range": (400000, 4000000)},
    "Construction":         {"risk_score": 7, "typical_turnover_range": (2000000, 20000000)},
    "Automobile Parts":     {"risk_score": 5, "typical_turnover_range": (1000000, 12000000)},
    "Pharmaceuticals":      {"risk_score": 3, "typical_turnover_range": (1500000, 15000000)},
    "Agriculture":          {"risk_score": 6, "typical_turnover_range": (300000, 3000000)},
    "Logistics":            {"risk_score": 4, "typical_turnover_range": (800000, 8000000)},
    "E-commerce":           {"risk_score": 3, "typical_turnover_range": (500000, 5000000)},
    "Real Estate":          {"risk_score": 8, "typical_turnover_range": (5000000, 50000000)},
    "Jewelry":              {"risk_score": 7, "typical_turnover_range": (2000000, 20000000)},
    "Chemical Trading":     {"risk_score": 6, "typical_turnover_range": (1000000, 10000000)},
    "Education Services":   {"risk_score": 2, "typical_turnover_range": (300000, 3000000)},
}

SECTOR_NAMES = list(SECTORS.keys())

# Sector probability distribution (must sum to 1.0)
SECTOR_WEIGHTS = [
    0.08, 0.12, 0.08, 0.07, 0.10,  # IT, Manufacturing, Textile, Food, Retail
    0.06, 0.05, 0.06, 0.08, 0.05,  # Construction, Auto, Pharma, Agriculture, Logistics
    0.07, 0.04, 0.03, 0.05, 0.06,  # E-commerce, Real Estate, Jewelry, Chemical, Education
]

# ─── Business Constitution Types ───────────────────────────────────────────────
CONSTITUTIONS = ["Proprietorship", "Partnership", "Private Limited", "LLP"]
CONSTITUTION_WEIGHTS = [0.60, 0.20, 0.15, 0.05]

# ─── Indian States with GST State Codes ────────────────────────────────────────
STATES = {
    "01": "Jammu & Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "27": "Maharashtra",
    "29": "Karnataka",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "36": "Telangana",
    "37": "Andhra Pradesh",
}

# Top business cities with state codes
BUSINESS_LOCATIONS = [
    {"city": "Mumbai",      "state_code": "27", "state": "Maharashtra"},
    {"city": "Delhi",       "state_code": "07", "state": "Delhi"},
    {"city": "Bangalore",   "state_code": "29", "state": "Karnataka"},
    {"city": "Hyderabad",   "state_code": "36", "state": "Telangana"},
    {"city": "Chennai",     "state_code": "33", "state": "Tamil Nadu"},
    {"city": "Kolkata",     "state_code": "19", "state": "West Bengal"},
    {"city": "Pune",        "state_code": "27", "state": "Maharashtra"},
    {"city": "Ahmedabad",   "state_code": "24", "state": "Gujarat"},
    {"city": "Jaipur",      "state_code": "08", "state": "Rajasthan"},
    {"city": "Lucknow",     "state_code": "09", "state": "Uttar Pradesh"},
    {"city": "Surat",       "state_code": "24", "state": "Gujarat"},
    {"city": "Indore",      "state_code": "23", "state": "Madhya Pradesh"},
    {"city": "Coimbatore",  "state_code": "33", "state": "Tamil Nadu"},
    {"city": "Nagpur",      "state_code": "27", "state": "Maharashtra"},
    {"city": "Ludhiana",    "state_code": "03", "state": "Punjab"},
]

# ─── Business Name Components ──────────────────────────────────────────────────
NAME_PREFIXES = [
    "Sri", "Shree", "Jai", "Om", "Royal", "New", "Golden", "Star",
    "National", "Prime", "Supreme", "Excel", "Apex", "Metro", "Global",
    "Pioneer", "United", "Modern", "Classic", "Eagle", "Diamond", "Pearl",
]

NAME_ROOTS = [
    "Lakshmi", "Ganesh", "Krishna", "Balaji", "Sai", "Durga", "Vinayak",
    "Sharma", "Patel", "Agarwal", "Gupta", "Singh", "Reddy", "Rao",
    "Kumar", "Enterprises", "Industries", "Associates", "Brothers", "Sons",
]

NAME_SUFFIXES = {
    "IT Services":       ["Tech", "Solutions", "Infotech", "Systems", "Software"],
    "Manufacturing":     ["Industries", "Manufacturing", "Works", "Fabricators", "Engineering"],
    "Textile":           ["Textiles", "Fabrics", "Garments", "Weaving", "Fashion"],
    "Food Processing":   ["Foods", "Agro", "Products", "Processors", "Spices"],
    "Retail Trade":      ["Traders", "Trading Co", "Mart", "Store", "Retail"],
    "Construction":      ["Constructions", "Builders", "Infrastructure", "Developers", "Realty"],
    "Automobile Parts":  ["Auto Parts", "Motors", "Auto Components", "Engineering", "Auto"],
    "Pharmaceuticals":   ["Pharma", "Healthcare", "Medicals", "Life Sciences", "Remedies"],
    "Agriculture":       ["Agri", "Farm Products", "Seeds", "Agro Industries", "Krishi"],
    "Logistics":         ["Logistics", "Transport", "Cargo", "Movers", "Freight"],
    "E-commerce":        ["Online", "Digital", "E-Store", "Marketplace", "Hub"],
    "Real Estate":       ["Realty", "Properties", "Estates", "Land Developers", "Homes"],
    "Jewelry":           ["Jewellers", "Gold", "Ornaments", "Gems", "Precious"],
    "Chemical Trading":  ["Chemicals", "Chem Industries", "Reagents", "Chemical Trading", "Polymers"],
    "Education Services": ["Academy", "Institute", "Education", "Learning", "Coaching"],
}

# ─── Distribution Parameters ───────────────────────────────────────────────────
# GMM parameters for base monthly revenue (in INR)
REVENUE_GMM_PARAMS = {
    "means": [50000, 150000, 400000, 1000000],
    "covariances": [15000**2, 50000**2, 120000**2, 300000**2],
    "weights": [0.30, 0.35, 0.25, 0.10],
}

# Business age distribution parameters (in years)
BUSINESS_AGE_PARAMS = {
    "min": 1,
    "max": 25,
    "mean": 6,
    "std": 4,
}

# Loan distribution parameters
LOAN_PARAMS = {
    "count_lambda": 2.0,         # Poisson λ for number of previous loans
    "size_mean": 500000,         # Mean loan size
    "size_std": 300000,          # Std dev loan size
    "default_rate_good": 0.05,   # Default rate for good businesses
    "default_rate_bad": 0.35,    # Default rate for fraudulent/risky
}

# GST filing parameters
GST_PARAMS = {
    "late_filing_lambda_good": 1.0,
    "late_filing_lambda_bad": 5.0,
    "cancellation_prob_good": 0.02,
    "cancellation_prob_bad": 0.25,
    "multi_registration_prob": 0.08,
}

# Time series parameters for sales patterns
TIMESERIES_PARAMS = {
    "seasonal": {
        "trend": 0.005,
        "seasonal_amplitude": 0.30,
        "noise_std": 0.08,
        "ar_coeff": 0.3,
    },
    "steady_growth": {
        "trend": 0.03,
        "seasonal_amplitude": 0.10,
        "noise_std": 0.05,
        "ar_coeff": 0.2,
    },
    "declining": {
        "trend": -0.025,
        "seasonal_amplitude": 0.15,
        "noise_std": 0.10,
        "ar_coeff": 0.25,
    },
    "fraudulent_spike": {
        "trend": 0.01,
        "seasonal_amplitude": 0.05,
        "noise_std": 0.06,
        "ar_coeff": 0.15,
        "spike_multiplier_range": (2.0, 5.0),
        "spike_month_range": (10, 30),
        "spike_duration": (1, 3),
    },
}

# Pattern assignment probabilities
SALES_PATTERN_WEIGHTS = {
    "non_fraud": [0.30, 0.40, 0.25, 0.05],  # seasonal, growth, decline, spike
    "fraud":     [0.10, 0.10, 0.20, 0.60],  # fraudulent businesses spike more
}

# Network parameters
NETWORK_PARAMS = {
    "vendor_count_alpha": 2.5,     # Power law exponent for vendors
    "vendor_count_min": 3,
    "vendor_count_max": 50,
    "customer_count_alpha": 2.0,
    "customer_count_min": 5,
    "customer_count_max": 100,
}

# Fraud injection rate
FRAUD_RATE = 0.18  # ~18% of businesses are fraudulent

# Credit score boundaries
CREDIT_SCORE_MIN = 300
CREDIT_SCORE_MAX = 900

# Decision engine thresholds
DECISION_THRESHOLDS = {
    "approve_min_score": 700,
    "approve_max_fraud": 0.20,
    "reject_min_fraud": 0.70,
    "reject_max_score": 450,
    "review_otherwise": True,
}
