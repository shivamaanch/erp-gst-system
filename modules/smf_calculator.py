from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

smf_bp = Blueprint("smf", __name__)

def calculate_smf_rate(fat: float, snf: float, base_fat_rate: float = 400,
                        base_snf_rate: float = 65) -> dict:
    """
    Milk SMF (Standard Milk Fat) Rate Calculator
    fat: fat % in milk
    snf: SNF % in milk
    base_fat_rate: price per kg fat (default ₹400)
    base_snf_rate: price per kg SNF (default ₹65)
    """
    fat_value = round((fat / 100) * base_fat_rate * 10, 4)   # per litre
    snf_value = round((snf / 100) * base_snf_rate * 10, 4)   # per litre
    total_rate = round(fat_value + snf_value, 4)
    return {
        "fat": fat, "snf": snf,
        "fat_value": fat_value, "snf_value": snf_value,
        "rate_per_litre": total_rate,
        "base_fat_rate": base_fat_rate,
        "base_snf_rate": base_snf_rate,
    }

@smf_bp.route("/smf")
@login_required
def index():
    return render_template("smf/index.html")

@smf_bp.route("/smf/calculate", methods=["POST"])
@login_required
def calculate():
    data = request.get_json()
    fat  = float(data.get("fat", 3.5))
    snf  = float(data.get("snf", 8.5))
    base_fat = float(data.get("base_fat_rate", 400))
    base_snf = float(data.get("base_snf_rate", 65))
    result = calculate_smf_rate(fat, snf, base_fat, base_snf)
    return jsonify(result)

@smf_bp.route("/smf/bulk", methods=["POST"])
@login_required
def bulk():
    entries = request.get_json().get("entries", [])
    results = []
    for e in entries:
        r = calculate_smf_rate(float(e.get("fat",3.5)), float(e.get("snf",8.5)),
                                float(e.get("base_fat_rate",400)), float(e.get("base_snf_rate",65)))
        r["name"] = e.get("name","")
        results.append(r)
    return jsonify(results)
