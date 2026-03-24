import re

def validate_gstin(gstin: str) -> tuple[bool, str]:
    gstin = gstin.strip().upper()
    if len(gstin) != 15:
        return False, "GSTIN must be 15 characters"
    pattern = r"^[0-3][0-9][A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$"
    if not re.match(pattern, gstin):
        return False, "Invalid GSTIN format"
    return True, "Valid"

def validate_pan(pan: str) -> tuple[bool, str]:
    pan = pan.strip().upper()
    if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan):
        return False, "Invalid PAN format"
    return True, "Valid"
