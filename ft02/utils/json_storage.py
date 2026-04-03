"""
JSON Storage Module

Handles serialization and persistence of business data to JSON files.
Custom encoder handles numpy types and datetime objects.
"""

import json
import os
import numpy as np
from datetime import datetime, date


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy and datetime types."""

    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)


def ensure_output_dirs(base_path: str):
    """Create output directory structure if it doesn't exist."""
    dirs = [
        os.path.join(base_path, "output", "data"),
        os.path.join(base_path, "output", "reports"),
        os.path.join(base_path, "output", "charts"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    return dirs


def save_all_businesses(businesses: list, filepath: str):
    """
    Save all generated businesses to a single JSON file.

    Args:
        businesses: List of business dictionaries
        filepath: Output file path
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(businesses, f, indent=2, cls=NumpyEncoder, ensure_ascii=False)

    print(f"[JSON] Saved {len(businesses)} businesses to {filepath}")


def load_all_businesses(filepath: str) -> list:
    """
    Load all businesses from a JSON file.

    Args:
        filepath: Path to business_data.json

    Returns:
        List of business dictionaries
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_single_business(business: dict, directory: str):
    """
    Save a single business to its own JSON file (keyed by GSTIN).

    Args:
        business: Business dictionary
        directory: Directory to save into
    """
    os.makedirs(directory, exist_ok=True)
    gstin = business.get("business_identity", {}).get("gstin", "unknown")
    filepath = os.path.join(directory, f"{gstin}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(business, f, indent=2, cls=NumpyEncoder, ensure_ascii=False)


def load_single_business(filepath: str) -> dict:
    """Load a single business from a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
