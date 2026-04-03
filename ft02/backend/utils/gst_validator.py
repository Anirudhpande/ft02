import re

def validate_gstin(gstin: str):

    pattern = r"\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]"

    if re.match(pattern, gstin):
        return True
    return False