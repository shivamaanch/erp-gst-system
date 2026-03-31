# modules/invoice.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify, Response
from flask_login import login_required, current_user
from extensions import db
from models import Bill, BillItem, Party, Item, Account, JournalHeader, JournalLine, FinancialYear, StockLedger
from sqlalchemy import func
from datetime import date, datetime
import json

invoice_bp = Blueprint("invoice", __name__)


def _fy_aliases(fy: str):
    if not fy:
        return []
    aliases = {fy}
    # Accept both 2025-26 and 25-26 style FY strings
    if len(fy) == 7 and fy[4] == "-":
        aliases.add(f"{fy[2:4]}-{fy[5:7]}")
    elif len(fy) == 5 and fy[2] == "-":
        aliases.add(f"20{fy}")
    return list(aliases)

def next_bill_no(cid, fy, bill_type):
    prefix = "SI" if bill_type == "Sales" else "PI"
    count = Bill.query.filter_by(company_id=cid, fin_year=fy, bill_type=bill_type).count()
    return f"{prefix}/{fy}/{str(count+1).zfill(4)}"

def money(v): return round(float(v or 0), 2)

@invoice_bp.route("/invoice")
@login_required
def index():
    cid  = session.get("company_id")
    fy   = session.get("fin_year")
    btype = request.args.get("type", "Sales")
    search = request.args.get("q","")
    fy_list = _fy_aliases(fy)
    q = Bill.query.filter(
        Bill.company_id == cid,
        Bill.bill_type == btype,
        Bill.is_cancelled == False,
    )
    if fy_list:
        q = q.filter(Bill.fin_year.in_(fy_list))
    if search:
        q = q.join(Party).filter(Party.name.ilike(f"%{search}%"))
    bills = q.order_by(Bill.bill_date.desc()).all()
    total = sum(b.total_amount for b in bills)
    return render_template("invoice/index.html", bills=bills, btype=btype, total=total, search=search)

@invoice_bp.route("/invoice/create/<btype>", methods=["GET","POST"])
@login_required
def create(btype):
    if btype not in ["Sales","Purchase"]:
        return redirect(url_for("invoice.index"))
    cid = session.get("company_id")
    fy  = session.get("fin_year")
    default_date = session.get("last_txn_date") or date.today().isoformat()
    party_types = ["Debtor", "Both", "Customer"] if btype=="Sales" else ["Creditor", "Supplier", "Both", "Vendor"]
    parties = Party.query.filter_by(company_id=cid, is_active=True).filter(
        Party.party_type.in_(party_types)
    ).order_by(Party.name).all()
    items = Item.query.filter_by(company_id=cid, is_active=True).order_by(Item.name).all() if hasattr(Item, "is_active") else Item.query.filter_by(company_id=cid).order_by(Item.name).all()

    if request.method == "POST":
        bill_no   = request.form.get("bill_no") or next_bill_no(cid, fy, btype)
        bill_date = datetime.strptime(request.form["bill_date"], "%Y-%m-%d").date()
        party_id  = int(request.form["party_id"])
        narration = request.form.get("narration","").strip()
        place_of_supply = request.form.get("place_of_supply","").strip()
        is_igst   = request.form.get("is_igst") == "on"

        item_ids  = request.form.getlist("item_id[]")
        qtys      = request.form.getlist("qty[]")
        rates     = request.form.getlist("rate[]")
        gst_rates = request.form.getlist("gst_rate[]")
        discs     = request.form.getlist("discount[]")

        if not item_ids:
            flash("Add at least one item!", "danger")
            return render_template("invoice/create.html", btype=btype, parties=parties, items=items,
                                   bill_no=next_bill_no(cid,fy,btype), today=default_date)

        bill = Bill(
            company_id=cid, fin_year=fy, bill_type=btype,
            bill_no=bill_no, bill_date=bill_date, party_id=party_id,
            narration=narration, is_cancelled=False, total_amount=0
        )
        if hasattr(bill, "place_of_supply"):
            bill.place_of_supply = place_of_supply
        db.session.add(bill)
        db.session.flush()

        total = 0
        for i, iid in enumerate(item_ids):
            if not iid: continue
            qty      = money(qtys[i])
            rate     = money(rates[i])
            gst_rate = money(gst_rates[i]) if i < len(gst_rates) else 0
            disc     = money(discs[i]) if i < len(discs) else 0
            taxable  = round(qty * rate * (1 - disc/100), 2)
            if is_igst:
                igst = round(taxable * gst_rate / 100, 2); cgst = sgst = 0
            else:
                cgst = sgst = round(taxable * gst_rate / 200, 2); igst = 0
            line_total = taxable + cgst + sgst + igst

            bi = BillItem(
                bill_id=bill.id,
                item_id=int(iid),
                qty=qty,
                rate=rate,
                taxable_amount=taxable,
                gst_rate=gst_rate,
                cgst=cgst,
                sgst=sgst,
                igst=igst,
            )
            if hasattr(bi, "discount"):       bi.discount = disc
            db.session.add(bi)
            total += line_total

            # Update stock
            try:
                sl = StockLedger(
                    company_id=cid,
                    fin_year=fy,
                    item_id=int(iid),
                    txn_date=bill_date,
                    txn_type=btype,
                    rate=rate,
                )
                if hasattr(sl, "in_qty"):
                    sl.in_qty = qty if btype == "Purchase" else 0
                if hasattr(sl, "out_qty"):
                    sl.out_qty = qty if btype == "Sales" else 0
                if hasattr(sl, "qty_in"):
                    sl.qty_in = qty if btype == "Purchase" else 0
                if hasattr(sl, "qty_out"):
                    sl.qty_out = qty if btype == "Sales" else 0
                if hasattr(sl, "bill_id"):
                    sl.bill_id = bill.id
                db.session.add(sl)
            except Exception:
                # Stock ledger is optional; do not block invoice creation
                pass

        bill.total_amount = round(total, 2)
        db.session.commit()
        session["last_txn_date"] = bill_date.isoformat()
        flash(f"{btype} invoice {bill.bill_no} created — ₹{bill.total_amount:,.2f}", "success")
        return redirect(url_for("invoice.view", bid=bill.id))

    return render_template("invoice/create.html", btype=btype, parties=parties, items=items,
                           bill_no=next_bill_no(cid,fy,btype), today=default_date)

@invoice_bp.route("/invoice/view/<int:bid>")
@login_required
def view(bid):
    cid  = session.get("company_id")
    bill = Bill.query.filter_by(id=bid, company_id=cid).first_or_404()
    return render_template("invoice/view.html", bill=bill)

@invoice_bp.route("/invoice/delete/<int:bid>", methods=["POST"])
@login_required
def delete(bid):
    """Delete an invoice and clear milk entry link if present"""
    cid = session.get("company_id")
    bill = Bill.query.filter_by(id=bid, company_id=cid).first_or_404()
    try:
        # Delete bill items first
        BillItem.query.filter_by(bill_id=bid).delete()
        # Find and delete any milk entry linked to this bill (not just clear bill_id)
        from models import MilkTransaction
        linked_milk = MilkTransaction.query.filter_by(bill_id=bid).first()
        if linked_milk:
            print(f"DEBUG: Deleting linked milk entry {linked_milk.id}")
            db.session.delete(linked_milk)
        # Delete the bill
        db.session.delete(bill)
        db.session.commit()
        print("DEBUG: Invoice and linked milk entry deleted successfully")
        flash(f"Invoice {bill.bill_no} deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete: {e}", "danger")
    return redirect(url_for("invoice.index", type=bill.bill_type))

@invoice_bp.route("/invoice/cancel/<int:bid>", methods=["POST"])
@login_required
def cancel(bid):
    cid  = session.get("company_id")
    bill = Bill.query.filter_by(id=bid, company_id=cid).first_or_404()
    bill.is_cancelled = True
    db.session.commit()
    flash(f"Invoice {bill.bill_no} cancelled.", "warning")
    return redirect(url_for("invoice.index", type=bill.bill_type))

@invoice_bp.route("/api/item-details/<int:iid>")
@login_required
def item_details(iid):
    cid  = session.get("company_id")
    item = Item.query.filter_by(id=iid, company_id=cid).first_or_404()
    return jsonify({
        "id": item.id, "name": item.name,
        "hsn": getattr(item,"hsn_code",""),
        "unit": getattr(item,"unit","Nos"),
        "gst_rate": float(getattr(item,"gst_rate",18)),
        "sale_rate": float(getattr(item,"sale_rate",0)),
        "purchase_rate": float(getattr(item,"purchase_rate",0))
    })
