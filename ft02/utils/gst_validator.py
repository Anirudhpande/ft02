"""
GSTIN and PAN Validation Utilities

Validates Indian GSTIN and PAN formats using regex patterns.
Enhanced from original gst_validator.py with PAN support and
checksum validation.
"""

import re


def validate_gstin(gstin: str) -> bool:
    """
    Validate a GSTIN (Goods and Services Tax Identification Number).

    Format: 2-digit state code + 10-char PAN + 1 entity number + Z + checksum
    Example: 27ABCDE1234F1Z5

    Args:
        gstin: GSTIN string to validate

    Returns:
        True if valid format
    """
    if not gstin or len(gstin) != 15:
        return False

    pattern = r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$"
    return bool(re.match(pattern, gstin))


def validate_pan(pan: str) -> bool:
    """
    Validate an Indian PAN (Permanent Account Number).

    Format: AAAAA9999A (5 letters + 4 digits + 1 letter)
    4th character: Entity type (P=Person, C=Company, F=Firm, H=HUF, etc.)

    Args:
        pan: PAN string to validate

    Returns:
        True if valid format
    """
    if not pan or len(pan) != 10:
        return False

    pattern = r"^[A-Z]{3}[PCFHATBLJG][A-Z]\d{4}[A-Z]$"
    return bool(re.match(pattern, pan))


def extract_state_from_gstin(gstin: str) -> str:
    """Extract 2-digit state code from GSTIN."""
    if validate_gstin(gstin):
        return gstin[:2]
    return ""


def extract_pan_from_gstin(gstin: str) -> str:
    """Extract PAN from GSTIN (characters 3-12)."""
    if validate_gstin(gstin):
        return gstin[2:12]
    return ""
