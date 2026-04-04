"""
GST Amnesty Scheme Configuration

Runtime-configurable amnesty windows that dynamically suppress
late-filing penalties for credit and fraud models — WITHOUT
retraining the models from scratch.

The approach works at the *feature-engineering layer*:
    1. Credit features:  `gst_compliance_score` is recalculated
       with late-filing contributions zeroed out.
    2. Fraud features:   `late_filings`, `months_not_filed`, and
       `filing_gap_score` are clamped to benign values.

Because the underlying ML models (XGBoost / LightGBM / Random-Forest /
Isolation-Forest) receive already-transformed features, the adjustment
propagates through the ensemble without touching model weights.
"""

from datetime import date
from typing import List, Optional

# ── In-memory amnesty register ──────────────────────────────────────────────────
# Each entry: { "quarter": "Q4-2025", "start": "2025-10-01", "end": "2025-12-31",
#               "description": "...", "active": True }

_amnesty_windows: List[dict] = []


# ── Public API ──────────────────────────────────────────────────────────────────

def register_amnesty_window(quarter: str, start_date: str,
                            end_date: str, description: str = "") -> dict:
    """
    Register a new GST amnesty quarter.

    Args:
        quarter:     Human label, e.g. "Q4-2025"
        start_date:  ISO date string  e.g. "2025-10-01"
        end_date:    ISO date string  e.g. "2025-12-31"
        description: Optional text shown on the dashboard

    Returns:
        The stored amnesty record.
    """
    record = {
        "quarter": quarter,
        "start": start_date,
        "end": end_date,
        "description": description or f"GST Amnesty Scheme for {quarter}",
        "active": True,
    }

    # Prevent duplicate quarters
    for i, w in enumerate(_amnesty_windows):
        if w["quarter"] == quarter:
            _amnesty_windows[i] = record
            return record

    _amnesty_windows.append(record)
    return record


def deactivate_amnesty_window(quarter: str) -> bool:
    """Deactivate (but don't delete) an amnesty window."""
    for w in _amnesty_windows:
        if w["quarter"] == quarter:
            w["active"] = False
            return True
    return False


def activate_amnesty_window(quarter: str) -> bool:
    """Re-activate a previously deactivated amnesty window."""
    for w in _amnesty_windows:
        if w["quarter"] == quarter:
            w["active"] = True
            return True
    return False


def get_active_amnesty_windows() -> List[dict]:
    """Return all currently active amnesty windows."""
    return [w for w in _amnesty_windows if w["active"]]


def get_all_amnesty_windows() -> List[dict]:
    """Return every registered amnesty window (active + inactive)."""
    return list(_amnesty_windows)


def is_date_in_amnesty(check_date: Optional[str] = None) -> bool:
    """
    Return True if `check_date` (or today) falls inside any
    active amnesty window.
    """
    if check_date:
        d = date.fromisoformat(check_date)
    else:
        d = date.today()

    for w in _amnesty_windows:
        if not w["active"]:
            continue
        try:
            ws = date.fromisoformat(w["start"])
            we = date.fromisoformat(w["end"])
            if ws <= d <= we:
                return True
        except (ValueError, TypeError):
            continue
    return False


def is_any_amnesty_active() -> bool:
    """
    Return True if any amnesty window is active at all —
    regardless of the current date.  Used by the feature builders
    so that late-filing penalties are suppressed whenever the operator
    has configured an amnesty scheme.
    """
    return any(w["active"] for w in _amnesty_windows)


def clear_all_amnesty_windows() -> None:
    """Remove all amnesty windows (useful for testing)."""
    _amnesty_windows.clear()


# ── Bootstrap a default amnesty if desired (optional) ────────────────────────
# Uncomment below to auto-register one on import:
# register_amnesty_window("Q4-2025", "2025-10-01", "2025-12-31",
#                          "Government amnesty for late GST filings")
