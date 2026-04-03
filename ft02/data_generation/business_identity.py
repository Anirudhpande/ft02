"""
Business Identity Generator

Generates realistic Indian business identities including GSTIN, PAN,
legal names, trade names, constitution types, and sector assignments.
Uses probabilistic distributions from constants module.
"""

import random
import string
import numpy as np
from datetime import datetime, timedelta

from utils.constants import (
    SECTORS, SECTOR_NAMES, SECTOR_WEIGHTS,
    CONSTITUTIONS, CONSTITUTION_WEIGHTS,
    BUSINESS_LOCATIONS,
    NAME_PREFIXES, NAME_ROOTS, NAME_SUFFIXES,
    BUSINESS_AGE_PARAMS,
)
from synthetic_models.gmm_engine import create_age_sampler


# Pre-build age sampler
_age_sampler = create_age_sampler(BUSINESS_AGE_PARAMS)


def generate_pan() -> str:
    """
    Generate a realistic Indian PAN number.
    Format: AAAAA9999A (5 letters + 4 digits + 1 letter)
    The 4th character indicates entity type:
      P = Individual, C = Company, F = Firm, H = HUF, etc.
    """
    first_three = ''.join(random.choices(string.ascii_uppercase, k=3))
    entity_type = random.choice(['P', 'C', 'F', 'H', 'A'])
    fifth_char = random.choice(string.ascii_uppercase)
    digits = ''.join(random.choices(string.digits, k=4))
    last_char = random.choice(string.ascii_uppercase)
    return f"{first_three}{entity_type}{fifth_char}{digits}{last_char}"


def generate_gstin(state_code: str, pan: str) -> str:
    """
    Generate a realistic GSTIN from state code and PAN.
    Format: 2-digit state code + 10-char PAN + 1 entity number + Z + checksum
    Example: 27ABCDE1234F1Z5
    """
    entity_num = str(random.randint(1, 9))
    check_char = random.choice(string.digits + string.ascii_uppercase)
    return f"{state_code}{pan}{entity_num}Z{check_char}"


def generate_business_name(sector: str) -> tuple:
    """
    Generate a realistic business name based on sector.

    Returns:
        (legal_name, trade_name)
    """
    prefix = random.choice(NAME_PREFIXES)
    root = random.choice(NAME_ROOTS)
    suffix = random.choice(NAME_SUFFIXES.get(sector, ["Enterprises"]))

    legal_name = f"{prefix} {root} {suffix}"

    # Trade name is sometimes shorter or different
    if random.random() < 0.4:
        trade_name = f"{root} {suffix}"
    else:
        trade_name = legal_name

    return legal_name, trade_name


def generate_business_identity(business_idx: int = 0) -> dict:
    """
    Generate a complete business identity profile.

    Args:
        business_idx: Index for seeding (optional)

    Returns:
        Dict with all identity fields
    """
    # Select sector based on probability weights
    sector = np.random.choice(SECTOR_NAMES, p=SECTOR_WEIGHTS)
    sector_info = SECTORS[sector]
    risk_sector_score = sector_info["risk_score"]

    # Select constitution
    constitution = np.random.choice(CONSTITUTIONS, p=CONSTITUTION_WEIGHTS)

    # Select location
    location = random.choice(BUSINESS_LOCATIONS)

    # Generate PAN and GSTIN
    pan = generate_pan()
    gstin = generate_gstin(location["state_code"], pan)

    # Generate business name
    legal_name, trade_name = generate_business_name(sector)

    # Generate business age (in years) using GMM sampler
    business_age = max(1, int(round(_age_sampler.sample_one())))

    # Calculate registration date from age
    today = datetime.now()
    reg_date = today - timedelta(days=business_age * 365 + random.randint(-180, 180))
    registration_date = reg_date.strftime("%Y-%m-%d")

    return {
        "gstin": gstin,
        "pan": pan,
        "legal_name": legal_name,
        "trade_name": trade_name,
        "business_constitution": constitution,
        "registration_date": registration_date,
        "business_age": business_age,
        "sector": sector,
        "business_location": f"{location['city']}, {location['state']}",
        "risk_sector_score": risk_sector_score,
    }
