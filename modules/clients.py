# modules/clients.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Party, Bill
clients_bp = Blueprint("clients", __name__)

PARTY_TYPES = ["Debtor", "Creditor", "Supplier", "Both"]

@clients_bp.route("/clients")
@login_required
def index():
    cid  = session.get("company_id")
    ptype = request.args.get("type", "")
    search = request.args.get("q", "")
    q = Party.query.filter_by(company_id=cid, is_active=True)
    if ptype:
        q = q.filter_by(party_type=ptype)
    if search:
        q = q.filter(Party.name.ilike(f"%{search}%"))
    parties = q.order_by(Party.name).all()
    return render_template("clients/index.html", parties=parties, ptype=ptype, search=search, party_types=PARTY_TYPES)

@clients_bp.route("/clients/add", methods=["GET","POST"])
@login_required
def add():
    cid = session.get("company_id")
    if request.method == "POST":
        p = Party(
            company_id   = cid,
            name         = request.form["name"].strip(),
            gstin        = request.form.get("gstin","").strip().upper() or None,
            party_type   = request.form["party_type"],
            phone        = request.form.get("phone","").strip() or None,
            email        = request.form.get("email","").strip() or None,
            address      = request.form.get("address","").strip() or None,
            pan          = request.form.get("pan","").strip().upper() or None,
            opening_balance = float(request.form.get("opening_balance") or 0),
            balance_type = request.form.get("balance_type","Dr"),
            is_active    = True
        )
        db.session.add(p)
        db.session.commit()
        flash(f"Party '{p.name}' added successfully!", "success")
        return redirect(url_for("clients.index"))
    return render_template("clients/form.html", party=None, party_types=PARTY_TYPES, title="Add Party")

@clients_bp.route("/clients/edit/<int:pid>", methods=["GET","POST"])
@login_required
def edit(pid):
    cid = session.get("company_id")
    p   = Party.query.filter_by(id=pid, company_id=cid).first_or_404()
    if request.method == "POST":
        p.name         = request.form["name"].strip()
        p.gstin        = request.form.get("gstin","").strip().upper() or None
        p.party_type   = request.form["party_type"]
        p.phone        = request.form.get("phone","").strip() or None
        p.email        = request.form.get("email","").strip() or None
        p.address      = request.form.get("address","").strip() or None
        p.pan          = request.form.get("pan","").strip().upper() or None
        p.opening_balance = float(request.form.get("opening_balance") or 0)
        p.balance_type = request.form.get("balance_type","Dr")
        db.session.commit()
        flash(f"Party '{p.name}' updated!", "success")
        return redirect(url_for("clients.index"))
    return render_template("clients/form.html", party=p, party_types=PARTY_TYPES, title="Edit Party")

@clients_bp.route("/clients/delete/<int:pid>", methods=["POST"])
@login_required
def delete(pid):
    cid = session.get("company_id")
    p   = Party.query.filter_by(id=pid, company_id=cid).first_or_404()
    p.is_active = False
    db.session.commit()
    flash(f"Party '{p.name}' deactivated.", "warning")
    return redirect(url_for("clients.index"))

@clients_bp.route("/clients/view/<int:pid>")
@login_required
def view(pid):
    cid = session.get("company_id")
    fy  = session.get("fin_year")
    p   = Party.query.filter_by(id=pid, company_id=cid).first_or_404()
    from models import Bill
    bills = Bill.query.filter_by(company_id=cid, party_id=pid, fin_year=fy, is_cancelled=False).order_by(Bill.bill_date.desc()).all()
    return render_template("clients/view.html", party=p, bills=bills)

@clients_bp.route("/api/party-search")
@login_required
def party_search():
    cid = session.get("company_id")
    q   = request.args.get("q","")
    ptype = request.args.get("type","")
    query = Party.query.filter_by(company_id=cid, is_active=True)
    if ptype:
        query = query.filter(Party.party_type.in_([ptype, "Both"]))
    if q:
        query = query.filter(Party.name.ilike(f"%{q}%"))
    results = [{"id": p.id, "name": p.name, "gstin": p.gstin or "", "type": p.party_type} for p in query.limit(20).all()]
    return jsonify(results)

@clients_bp.route("/clients/quick-add", methods=["POST"])
@login_required
def quick_add():
    try:
        cid = session.get("company_id")
        name = request.form.get("name","").strip()
        if not name:
            return jsonify({"success": False, "error": "Party name required"}), 400
        
        p = Party(
            company_id=cid,
            name=name,
            gstin=request.form.get("gstin","").strip().upper() or None,
            phone=request.form.get("phone","").strip() or None,
            party_type=request.form.get("party_type","Customer"),
            is_active=True
        )
        db.session.add(p)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "party": {
                "id": p.id,
                "name": p.name,
                "gstin": p.gstin or "",
                "phone": p.phone or ""
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@clients_bp.route("/clients/quick-add-item", methods=["POST"])
@login_required
def quick_add_item():
    try:
        from models import Item
        cid = session.get("company_id")
        name = request.form.get("name","").strip()
        if not name:
            return jsonify({"success": False, "error": "Item name required"}), 400
        
        item = Item(
            company_id=cid,
            name=name,
            hsn_code=request.form.get("hsn_code","").strip() or None,
            unit=request.form.get("unit","Nos"),
            gst_rate=float(request.form.get("gst_rate",18)),
            sale_rate=float(request.form.get("sale_rate",0)),
            purchase_rate=float(request.form.get("purchase_rate",0)),
            is_active=True
        )
        db.session.add(item)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "item": {
                "id": item.id,
                "name": item.name,
                "hsn_code": item.hsn_code or "",
                "unit": item.unit or "Nos",
                "gst_rate": float(item.gst_rate or 18),
                "sale_rate": float(item.sale_rate or 0),
                "purchase_rate": float(item.purchase_rate or 0)
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
