from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required
from datetime import date, datetime
from models import db, Party, Bill, BillItem

psi_bp = Blueprint('psi', __name__, url_prefix='/psi')

@psi_bp.route("/purchase", methods=["GET","POST"])
@login_required
def purchase_form():
    cid = session.get("company_id")
    parties = Party.query.filter_by(company_id=cid, is_active=True).order_by(Party.name).all()
    
    if request.method == "POST":
        party_id = int(request.form["party_id"])
        invoice_date = datetime.strptime(request.form["invoice_date"], "%Y-%m-%d").date()
        bill_no = request.form.get("bill_no", "").strip()
        
        # Generate auto bill number if not provided
        if not bill_no:
            # Get financial year from session
            fy = session.get("fin_year", "25-26")
            # Get next purchase bill number
            last_bill = Bill.query.filter_by(company_id=cid, bill_type="Purchase").order_by(Bill.id.desc()).first()
            next_num = (last_bill.id + 1) if last_bill else 1
            bill_no = f"P/{str(next_num).zfill(4)}/{fy}"
        
        # Create purchase invoice
        bill = Bill(
            company_id=cid,
            party_id=party_id,
            bill_no=bill_no,
            bill_date=invoice_date,
            bill_type="Purchase",
            taxable_amount=0,
            cgst=0,
            sgst=0,
            igst=0,
            total_amount=0,
            narration="Purchase Invoice"
        )
        db.session.add(bill)
        db.session.commit()
        
        flash(f"Purchase Invoice {bill_no} created successfully", "success")
        return redirect(url_for("psi.purchase_list"))
    
    return render_template("psi/purchase_form.html", parties=parties, today=date.today().isoformat())

@psi_bp.route("/purchase/list")
@login_required
def purchase_list():
    cid = session.get("company_id")
    invoices = Bill.query.filter_by(company_id=cid, bill_type="Purchase").order_by(Bill.bill_date.desc()).all()
    return render_template("psi/purchase_list.html", invoices=invoices)
