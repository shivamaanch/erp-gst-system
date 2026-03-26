from flask import Blueprint, request, jsonify, session
from models import db, Party, Company
from flask_login import login_required

parties_bp = Blueprint('parties', __name__)

@parties_bp.route("/parties/add", methods=["POST"])
def add_party():
    """Add a new party via AJAX"""
    try:
        cid = session.get("company_id", 1)
        
        party = Party(
            company_id=cid,
            name=request.form.get("name"),
            phone=request.form.get("phone"),
            email=request.form.get("email"),
            gstin=request.form.get("gst_number"),
            address=request.form.get("address"),
            state_code=request.form.get("state"),
            is_active=True if request.form.get("is_active") else False
        )
        
        db.session.add(party)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "id": party.id,
            "name": party.name,
            "phone": party.phone,
            "address": party.address,
            "message": "Party added successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        })

@parties_bp.route("/parties/list")
@login_required
def list_parties():
    """Get list of parties for autocomplete"""
    cid = session.get("company_id", 1)
    parties = Party.query.filter_by(company_id=cid, is_active=True).order_by(Party.name).all()
    
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "phone": p.phone,
        "address": p.address
    } for p in parties])
