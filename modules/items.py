# modules/items.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify
from flask_login import login_required
from extensions import db
from models import Item

items_bp = Blueprint("items", __name__)

@items_bp.route("/items")
@login_required
def index():
    cid = session.get("company_id")
    search = request.args.get("q", "")
    query = Item.query.filter_by(company_id=cid, is_active=True)
    if search:
        query = query.filter(Item.name.ilike(f"%{search}%"))
    items = query.order_by(Item.name).all()
    return render_template("items/index.html", items=items, search=search)

@items_bp.route("/items/add", methods=["GET", "POST"])
@login_required
def add():
    cid = session.get("company_id")
    if request.method == "POST":
        item = Item(
            company_id=cid,
            name=request.form["name"].strip(),
            hsn_code=request.form.get("hsn_code", "").strip() or None,
            unit=request.form.get("unit", "Nos"),
            gst_rate=float(request.form.get("gst_rate", 18)),
            purchase_rate=float(request.form.get("purchase_rate", 0)),
            sale_rate=float(request.form.get("sale_rate", 0)),
            is_active=True
        )
        db.session.add(item)
        db.session.commit()
        flash(f"Item '{item.name}' added successfully!", "success")
        return redirect(url_for("items.index"))
    return render_template("items/form.html", item=None, title="Add Item")

@items_bp.route("/items/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
def edit(item_id):
    cid = session.get("company_id")
    item = Item.query.filter_by(id=item_id, company_id=cid).first_or_404()
    if request.method == "POST":
        item.name = request.form["name"].strip()
        item.hsn_code = request.form.get("hsn_code", "").strip() or None
        item.unit = request.form.get("unit", "Nos")
        item.gst_rate = float(request.form.get("gst_rate", 18))
        item.purchase_rate = float(request.form.get("purchase_rate", 0))
        item.sale_rate = float(request.form.get("sale_rate", 0))
        db.session.commit()
        flash(f"Item '{item.name}' updated!", "success")
        return redirect(url_for("items.index"))
    return render_template("items/form.html", item=item, title="Edit Item")

@items_bp.route("/items/delete/<int:item_id>", methods=["POST"])
@login_required
def delete(item_id):
    cid = session.get("company_id")
    item = Item.query.filter_by(id=item_id, company_id=cid).first_or_404()
    item.is_active = False
    db.session.commit()
    flash(f"Item '{item.name}' deactivated.", "warning")
    return redirect(url_for("items.index"))
