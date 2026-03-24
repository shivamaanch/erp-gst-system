from flask import Blueprint, request, jsonify
import re

validator_bp = Blueprint("validator", __name__)

def validate_gstin(gstin: str):
    gstin = gstin.strip().upper()
    if len(gstin) != 15: return False, "Must be 15 characters"
    if not re.match(r"^[0-3][0-9][A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$", gstin):
        return False, "Invalid format"
    return True, "Valid GSTIN"

def validate_pan(pan: str):
    pan = pan.strip().upper()
    if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan):
        return False, "Invalid PAN format"
    return True, "Valid PAN"

def validate_ifsc(ifsc: str):
    ifsc = ifsc.strip().upper()
    if not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", ifsc):
        return False, "Invalid IFSC format"
    return True, "Valid IFSC"

@validator_bp.route("/validate/gstin")
def check_gstin():
    g = request.args.get("gstin","")
    ok, msg = validate_gstin(g)
    return jsonify({"valid": ok, "message": msg, "gstin": g.upper()})

@validator_bp.route("/validate/pan")
def check_pan():
    p = request.args.get("pan","")
    ok, msg = validate_pan(p)
    return jsonify({"valid": ok, "message": msg})

@validator_bp.route("/validate/ifsc")
def check_ifsc():
    i = request.args.get("ifsc","")
    ok, msg = validate_ifsc(i)
    return jsonify({"valid": ok, "message": msg})
