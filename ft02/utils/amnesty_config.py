"""
GST Amnesty Scheme Configuration Manager (Twist 2)
In-memory register of active amnesty windows to suppress penalties at runtime.
"""
from datetime import datetime
from typing import List, Dict, Optional

# Active amnesty windows register
# Records format: {"quarter": "Q4-2025", "start": datetime, "end": datetime, "description": "", "active": True}
_AMNESTY_WINDOWS: List[Dict] = []


def register_amnesty_window(quarter: str, start_date: str, end_date: str, description: str = "") -> dict:
    """Register a new amnesty quarter window."""
    record = {
        "quarter": quarter,
        "start": datetime.fromisoformat(start_date),
        "end": datetime.fromisoformat(end_date),
        "description": description,
        "active": True,
    }
    # Replace if exists, else append
    for i, w in enumerate(_AMNESTY_WINDOWS):
        if w["quarter"] == quarter:
            _AMNESTY_WINDOWS[i] = record
            return record
    
    _AMNESTY_WINDOWS.append(record)
    return record


def deactivate_amnesty_window(quarter: str) -> bool:
    """Deactivate an amnesty window."""
    for w in _AMNESTY_WINDOWS:
        if w["quarter"] == quarter:
            w["active"] = False
            return True
    return False


def activate_amnesty_window(quarter: str) -> bool:
    """Re-activate an amnesty window."""
    for w in _AMNESTY_WINDOWS:
        if w["quarter"] == quarter:
            w["active"] = True
            return True
    return False


def is_any_amnesty_active() -> bool:
    """Global check if any registered amnesty window covers the current date."""
    now = datetime.now()
    for w in _AMNESTY_WINDOWS:
        if w["active"] and w["start"] <= now <= w["end"]:
            return True
    return False


def get_active_amnesty_windows() -> List[dict]:
    """Get details of currently active amnesty windows."""
    now = datetime.now()
    active = []
    for w in _AMNESTY_WINDOWS:
        if w["active"] and w["start"] <= now <= w["end"]:
            active.append({
                "quarter": w["quarter"],
                "start": w["start"].isoformat(),
                "end": w["end"].isoformat(),
                "description": w["description"]
            })
    return active


def get_all_amnesty_windows() -> List[dict]:
    """Get all registered amnesty windows."""
    return [
        {
            "quarter": w["quarter"],
            "start": w["start"].isoformat(),
            "end": w["end"].isoformat(),
            "description": w["description"],
            "active": w["active"]
        } for w in _AMNESTY_WINDOWS
    ]
