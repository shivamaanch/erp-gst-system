import re

GSTIN_RE = re.compile(r"^[0-3][0-9][A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
PAN_RE   = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")

def is_valid_gstin(g: str) -> bool:
    return bool(GSTIN_RE.match(g.strip().upper())) if g else False

def is_valid_pan(p: str) -> bool:
    return bool(PAN_RE.match(p.strip().upper())) if p else False

def gstin_to_pan(gstin: str) -> str:
    return gstin[2:12] if len(gstin) == 15 else ""

def gstin_state_code(gstin: str) -> str:
    STATE_CODES = {
        "01":"J&K","02":"HP","03":"Punjab","04":"Chandigarh","05":"Uttarakhand",
        "06":"Haryana","07":"Delhi","08":"Rajasthan","09":"UP","10":"Bihar",
        "11":"Sikkim","12":"AP","13":"Nagaland","14":"Manipur","15":"Mizoram",
        "16":"Tripura","17":"Meghalaya","18":"Assam","19":"WB","20":"Jharkhand",
        "21":"Odisha","22":"CG","23":"MP","24":"Gujarat","27":"Maharashtra",
        "29":"Karnataka","32":"Kerala","33":"TN","36":"Telangana","37":"AP(New)",
    }
    code = gstin[:2] if len(gstin) >= 2 else ""
    return STATE_CODES.get(code, f"State {code}")
