from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify
from flask_login import login_required
from extensions import db
from models import MilkRateChart, MilkTransaction, Party, Bill, BillItem
from datetime import date, datetime

milk_bp = Blueprint("milk", __name__)

def calc_rate(fat, snf, fat_rate, snf_rate):
    return round(float(fat)*float(fat_rate) + float(snf)*float(snf_rate), 4)

def next_bill_no(company_id, fin_year, bill_type):
    prefix = "MLK-S" if bill_type == "Sales" else "MLK-P"
    last = Bill.query.filter(Bill.company_id==company_id, Bill.fin_year==fin_year, Bill.bill_no.like(f"{prefix}%")).order_by(Bill.id.desc()).first()
    num = 1
    if last:
        try: num = int(last.bill_no.split("-")[-1]) + 1
        except: num = 1
    return f"{prefix}-{num:04d}"

@milk_bp.route("/milk/rates")
@login_required
def rates():
    cid = session.get("company_id")
    charts = MilkRateChart.query.filter_by(company_id=cid, is_active=True).order_by(MilkRateChart.effective_date.desc()).all()
    return render_template("milk/rates_traditional.html", charts=charts)

@milk_bp.route("/milk/rates/add", methods=["GET","POST"])
@login_required
def add_rate():
    cid = session.get("company_id")
    if request.method == "POST":
        rc = MilkRateChart(
            company_id=cid, chart_name=request.form["chart_name"].strip(),
            effective_date=datetime.strptime(request.form["effective_date"],"%Y-%m-%d").date(),
            fat_rate=float(request.form["fat_rate"]), snf_rate=float(request.form["snf_rate"]),
            base_fat=float(request.form.get("base_fat") or 0),
            base_snf=float(request.form.get("base_snf") or 0),
            txn_type=request.form.get("txn_type","Both"), is_active=True)
        db.session.add(rc); db.session.commit()
        flash("Rate chart saved!", "success")
        return redirect(url_for("milk.rates"))
    return render_template("milk/rate_form_traditional.html", chart=None, today=date.today().isoformat())

@milk_bp.route("/milk/rates/edit/<int:cid_>", methods=["GET","POST"])
@login_required
def edit_rate(cid_):
    cid   = session.get("company_id")
    chart = MilkRateChart.query.filter_by(id=cid_, company_id=cid).first_or_404()
    if request.method == "POST":
        chart.chart_name=request.form["chart_name"].strip()
        chart.effective_date=datetime.strptime(request.form["effective_date"],"%Y-%m-%d").date()
        chart.fat_rate=float(request.form["fat_rate"]); chart.snf_rate=float(request.form["snf_rate"])
        chart.base_fat=float(request.form.get("base_fat") or 0)
        chart.base_snf=float(request.form.get("base_snf") or 0)
        chart.txn_type=request.form.get("txn_type","Both")
        db.session.commit(); flash("Updated!", "success")
        return redirect(url_for("milk.rates"))
    return render_template("milk/rate_form_traditional.html", chart=chart, today=date.today().isoformat())

@milk_bp.route("/milk/entry", methods=["GET"])
def entry_list():
    # Initialize session if not set
    if not session.get("company_id"):
        session["company_id"] = 1
        session["company_name"] = "Default Company"
        session["fin_year"] = "2025-26"
        session["user_role"] = "admin"
    
    cid = session.get("company_id"); fy = session.get("fin_year")
    
    # Use only raw SQL query to avoid ALL SQLAlchemy ORM issues
    from sqlalchemy import text
    sql = """
    SELECT id, company_id, fin_year, voucher_no, party_id, txn_date, shift, 
           txn_type, qty_liters, fat, snf, rate, amount, chart_id, narration, bill_id
    FROM milk_transactions 
    WHERE company_id = :company_id AND fin_year = :fin_year 
    ORDER BY txn_date DESC 
    LIMIT 200
    """
    result = db.session.execute(text(sql), {"company_id": cid, "fin_year": fy})
    txns = []
    for row in result:
        # Create a simple object with the data
        class SimpleMilkTransaction:
            def __init__(self, row):
                self.id = row.id
                self.company_id = row.company_id
                self.fin_year = row.fin_year
                self.voucher_no = row.voucher_no
                self.party_id = row.party_id
                self.txn_date = row.txn_date
                self.shift = row.shift
                self.txn_type = row.txn_type
                self.qty_liters = row.qty_liters
                self.fat = row.fat
                self.snf = row.snf
                self.clr = 0.0  # Default CLR value
                self.rate = row.rate
                self.amount = row.amount
                self.chart_id = row.chart_id
                self.narration = row.narration
                self.bill_id = row.bill_id
        
        txns.append(SimpleMilkTransaction(row))
    total_qty = sum(float(t.qty_liters) for t in txns)
    total_amt = sum(float(t.amount) for t in txns)
    # Calculate averages and totals for template
    avg_fat = sum(t.fat for t in txns) / len(txns) if txns else 0
    avg_snf = sum(t.snf for t in txns) / len(txns) if txns else 0
    total_bf_kgs = sum(t.qty_liters * t.fat / 100 for t in txns)
    total_snf_kgs = sum(t.qty_liters * t.snf / 100 for t in txns)
    
    # Get parties for filter dropdown
    parties = Party.query.filter_by(company_id=cid, is_active=True).order_by(Party.name).all()
    
    return render_template("milk/entry_list_traditional.html", 
                     txns=txns, total_qty=total_qty, total_amt=total_amt,
                     avg_fat=avg_fat, avg_snf=avg_snf,
                     total_bf_kgs=total_bf_kgs, total_snf_kgs=total_snf_kgs,
                     parties=parties)

@milk_bp.route("/milk/entry/add", methods=["GET","POST"])
def add_entry():
    # Initialize session if not set
    if not session.get("company_id"):
        session["company_id"] = 1
        session["company_name"] = "Default Company"
        session["fin_year"] = "2025-26"
        session["user_role"] = "admin"
    
    cid = session.get("company_id"); fy = session.get("fin_year")
    parties = Party.query.filter_by(company_id=cid, is_active=True).order_by(Party.name).all()
    charts  = MilkRateChart.query.filter_by(company_id=cid, is_active=True).order_by(MilkRateChart.effective_date.desc()).all()
    
    if request.method == "POST":
        fat=float(request.form["fat"]) 
        snf=float(request.form.get("snf", request.form.get("snf_auto", 8.5)))
        qty=float(request.form["qty_liters"])
        
        # Handle rate chart selection
        chart_id=request.form.get("chart_id")
        if chart_id and chart_id != "":
            chart=MilkRateChart.query.get(int(chart_id))
            fat_rate=chart.fat_rate; snf_rate=chart.snf_rate
        else:
            fat_rate=float(request.form.get("fat_rate", 200))
            snf_rate=float(request.form.get("snf_rate", 100))
        
        # Prefer front-end calculated amount / rate if provided
        amount_str = (request.form.get("amount") or "").strip()
        calc_rate_str = (request.form.get("calc_rate") or "").strip()
        if amount_str:
            amount = float(amount_str)
            if calc_rate_str:
                rate = float(calc_rate_str)
            else:
                rate = round(amount / qty, 4) if qty else 0
        else:
            # Fallback: use daily rate or traditional component method
            daily_rate = float(request.form.get("rate_per_liter", 0))
            if daily_rate > 0:
                # Derive BF/SNF component rates from base price using 60:40 split
                fat_share = 0.60
                snf_share = 0.40
                std_fat_kg = 6.5
                std_snf_kg = 8.5

                bf_rate = (daily_rate * fat_share) / std_fat_kg
                snf_rate = (daily_rate * snf_share) / std_snf_kg

                bf_kgs = qty * fat / 100.0
                snf_kgs = qty * snf / 100.0
                amount = round(bf_kgs * bf_rate + snf_kgs * snf_rate, 2)
                rate = round(amount / qty, 4) if qty else 0
            else:
                rate = calc_rate(fat, snf, fat_rate, snf_rate)
                amount = round(rate * qty, 2)
        
        txn_type=request.form["txn_type"]; 
        party_id_str = request.form.get("party_id", "").strip()
        if not party_id_str:
            flash("Please select a party", "error")
            return redirect(url_for('milk.add_entry'))
        party_id=int(party_id_str)
        txn_date=datetime.strptime(request.form["txn_date"],"%Y-%m-%d").date()
        create_invoice=request.form.get("create_invoice")=="1"
        txn=MilkTransaction(company_id=cid,fin_year=fy,party_id=party_id,txn_date=txn_date,
            shift=request.form.get("shift","Morning"),txn_type=txn_type,
            qty_liters=qty,fat=fat,snf=snf,clr=float(request.form.get("clr",0)),rate=rate,amount=amount,
            chart_id=chart_id,narration=request.form.get("narration","").strip())
        db.session.add(txn)
        bill_no=None
        if create_invoice:
            bill_type="Sales" if txn_type=="Sale" else "Purchase"
            # Use manual invoice number if provided, otherwise generate automatic
            manual_bill_no = request.form.get("manual_bill_no", "").strip()
            if manual_bill_no:
                bill_no = manual_bill_no
            else:
                # Generate bill number in P/0001/25-26 format
                last_bill = Bill.query.filter_by(company_id=cid, bill_type=bill_type).order_by(Bill.id.desc()).first()
                next_num = (last_bill.id + 1) if last_bill else 1
                prefix = "P" if bill_type == "Purchase" else "S"
                bill_no = f"{prefix}/{str(next_num).zfill(4)}/{fy}"
            gst_rate=float(request.form.get("gst_rate") or 0)
            gst_amt=round(amount*gst_rate/100,2); total=round(amount+gst_amt,2)
            bill=Bill(company_id=cid,fin_year=fy,party_id=party_id,bill_no=bill_no,
                bill_date=txn_date,bill_type=bill_type,taxable_amount=amount,
                cgst=gst_amt/2, sgst=gst_amt/2, igst=0, total_amount=total,
                narration=f"Milk {txn_type} | FAT:{fat}% SNF:{snf}% | {qty}L @ Rs{rate}/L",
                is_cancelled=False)
            db.session.add(bill); db.session.flush()
            item=BillItem(bill_id=bill.id,qty=qty,rate=rate,taxable_amount=amount,
                gst_rate=gst_rate,cgst=gst_amt/2,sgst=gst_amt/2,igst=0)
            db.session.add(item); txn.bill_id=bill.id
        db.session.commit()
        msg=f"Saved {qty}L @ Rs{rate}/L = Rs{amount}"
        if bill_no: msg+=f" | Invoice {bill_no} created"
        flash(msg,"success")
        return redirect(url_for("milk.entry_list"))
        
    return render_template("milk/entry_form_traditional.html", parties=parties, charts=charts, today=date.today().isoformat())

@milk_bp.route("/milk/entry/<int:txn_id>/edit", methods=["GET","POST"])
@login_required
def edit_entry(txn_id):
    cid     = session.get("company_id"); fy = session.get("fin_year")
    parties = Party.query.filter_by(company_id=cid, is_active=True).order_by(Party.name).all()
    charts  = MilkRateChart.query.filter_by(company_id=cid, is_active=True).order_by(MilkRateChart.effective_date.desc()).all()
    
    # Get existing transaction
    txn = MilkTransaction.query.filter_by(id=txn_id, company_id=cid, fin_year=fy).first_or_404()
    
    if request.method == "POST":
        # Update transaction with form data
        txn.txn_date = datetime.strptime(request.form["txn_date"], "%Y-%m-%d").date()
        txn.shift = request.form["shift"]
        txn.txn_type = request.form["txn_type"]
        txn.party_id = int(request.form["party_id"])
        txn.qty_liters = float(request.form["qty_liters"])
        txn.fat = float(request.form["fat"])
        txn.clr = float(request.form["clr"])
        txn.snf = float(request.form.get("snf_auto", 8.5))

        # Prefer front-end calculated rate / amount
        calc_rate_str = (request.form.get("calc_rate") or "").strip()
        amount_str = (request.form.get("amount") or "").strip()

        if calc_rate_str:
            txn.rate = float(calc_rate_str)
        else:
            daily_rate = float(request.form.get("rate_per_liter", 0))
            if daily_rate > 0:
                txn.rate = daily_rate

        if amount_str:
            txn.amount = float(amount_str)
        else:
            # Recalculate amount from components using the same 60:40 logic
            qty = txn.qty_liters
            fat = txn.fat
            snf = txn.snf

            # Reconstruct component rates from a base price if available
            daily_rate = float(request.form.get("rate_per_liter", 0))
            if daily_rate <= 0:
                # Fallback: approximate base price from current rate if possible
                # This keeps old data usable even if we don't know the original 100 kg price
                daily_rate = txn.rate * 100  # rough back-calculation

            fat_share = 0.60
            snf_share = 0.40
            std_fat_kg = 6.5
            std_snf_kg = 8.5

            bf_rate = (daily_rate * fat_share) / std_fat_kg
            snf_rate = (daily_rate * snf_share) / std_snf_kg

            bf_kgs = qty * fat / 100.0
            snf_kgs = qty * snf / 100.0
            txn.amount = round(bf_kgs * bf_rate + snf_kgs * snf_rate, 2)
        txn.narration = request.form.get("narration", "").strip()
        
        # Handle invoice creation/update
        create_invoice = request.form.get("create_invoice") == "on"
        if create_invoice and not txn.bill_id:
            # Create new invoice
            bill_type="Sales" if txn.txn_type=="Sale" else "Purchase"
            # Use manual invoice number if provided, otherwise generate automatic
            manual_bill_no = request.form.get("manual_bill_no", "").strip()
            if manual_bill_no:
                bill_no = manual_bill_no
            else:
                # Generate bill number in P/0001/25-26 format
                last_bill = Bill.query.filter_by(company_id=cid, bill_type=bill_type).order_by(Bill.id.desc()).first()
                next_num = (last_bill.id + 1) if last_bill else 1
                prefix = "P" if bill_type == "Purchase" else "S"
                bill_no = f"{prefix}/{str(next_num).zfill(4)}/{fy}"
            gst_rate=float(request.form.get("gst_rate") or 0)
            gst_amt=round(txn.amount*gst_rate/100,2); total=round(txn.amount+gst_amt,2)
            bill=Bill(company_id=cid,fin_year=fy,party_id=txn.party_id,bill_no=bill_no,
                bill_date=txn.txn_date,bill_type=bill_type,taxable_amount=txn.amount,
                cgst=gst_amt/2, sgst=gst_amt/2, igst=0, total_amount=total,
                narration=txn.narration, is_cancelled=False)
            db.session.add(bill); db.session.flush()
            item=BillItem(bill_id=bill.id,qty=txn.qty_liters,rate=txn.rate,taxable_amount=txn.amount,
                gst_rate=gst_rate,cgst=gst_amt/2,sgst=gst_amt/2,igst=0)
            db.session.add(item); txn.bill_id=bill.id
        
        db.session.commit()
        flash(f"Milk entry updated successfully", "success")
        return redirect(url_for("milk.entry_list"))
    
    # Pre-fill form with existing data
    return render_template("milk/entry_form_traditional.html", 
                     parties=parties, charts=charts, 
                     txn=txn, edit_mode=True,
                     today=txn.txn_date.isoformat())

@milk_bp.route("/milk/entry/<int:txn_id>/update-field", methods=["POST"])
@login_required
def update_field(txn_id):
    cid = session.get("company_id"); fy = session.get("fin_year")
    txn = MilkTransaction.query.filter_by(id=txn_id, company_id=cid, fin_year=fy).first_or_404()
    
    data = request.get_json()
    field = data.get("field")
    value = data.get("value")
    
    try:
        # Update the specific field
        if field == "qty_liters":
            txn.qty_liters = float(value)
        elif field == "fat":
            txn.fat = float(value)
        elif field == "snf":
            txn.snf = float(value)
        elif field == "rate":
            txn.rate = float(value)
            txn.rate_per_liter = float(value)
        
        # Recalculate amount
        txn.amount = txn.qty_liters * txn.rate
        
        db.session.commit()
        return jsonify({"success": True, "message": "Updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})

@milk_bp.route("/api/milk-rate")
@login_required
def api_rate():
    cid=session.get("company_id"); chart_id=request.args.get("chart_id")
    fat=float(request.args.get("fat",0)); snf=float(request.args.get("snf",0))
    qty=float(request.args.get("qty",0))
    chart=MilkRateChart.query.filter_by(id=chart_id,company_id=cid).first()
    if not chart: return jsonify({"rate":0,"amount":0})
    rate=calc_rate(fat,snf,chart.fat_rate,chart.snf_rate)
    return jsonify({"rate":rate,"amount":round(rate*qty,2)})

@milk_bp.route("/milk/invoice/<int:bill_id>")
@login_required
def view_invoice(bill_id):
    """View milk invoice"""
    cid = session.get("company_id")
    
    # Get bill and related transaction
    bill = Bill.query.filter_by(id=bill_id, company_id=cid).first_or_404()
    milk_transaction = MilkTransaction.query.filter_by(bill_id=bill_id).first()
    
    # Get company from session
    from models import Company
    company = Company.query.get(cid)
    
    # Convert Decimal to float for template calculations
    def decimal_to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    
    return render_template("milk/invoice_view.html", 
                         bill=bill, 
                         milk_transaction=milk_transaction,
                         company=company,
                         float=decimal_to_float)

@milk_bp.route("/milk/summary")
@login_required
def summary():
    cid=session.get("company_id"); fy=session.get("fin_year")
    from sqlalchemy import func
    data=db.session.query(MilkTransaction.txn_type,Party.name,
        func.sum(MilkTransaction.qty_liters).label("total_qty"),
        func.sum(MilkTransaction.amount).label("total_amt"),
        func.avg(MilkTransaction.fat).label("avg_fat"),
        func.avg(MilkTransaction.snf).label("avg_snf"),
    ).join(Party,MilkTransaction.party_id==Party.id).filter(
        MilkTransaction.company_id==cid,MilkTransaction.fin_year==fy
    ).group_by(MilkTransaction.txn_type,Party.name).all()
    # Calculate traditional summary data
    traditional_data = []
    for row in data:
        total_qty = float(row.total_qty)
        avg_fat = float(row.avg_fat)
        avg_snf = float(row.avg_snf)
        total_amt = float(row.total_amt)
        
        # Calculate component weights
        total_bf_kgs = total_qty * avg_fat / 100
        total_snf_kgs = total_qty * avg_snf / 100
        
        # Calculate ratio and rate per liter
        ratio = (total_snf_kgs / total_bf_kgs) if total_bf_kgs > 0 else 0
        rate_per_liter = (total_amt / total_qty) if total_qty > 0 else 0
        
        traditional_data.append({
            'txn_type': row.txn_type,
            'name': row.name,
            'total_qty': total_qty,
            'avg_fat': avg_fat,
            'avg_snf': avg_snf,
            'total_bf_kgs': total_bf_kgs,
            'total_snf_kgs': total_snf_kgs,
            'ratio': ratio,
            'rate_per_liter': rate_per_liter,
            'total_amt': total_amt,
        })
    
    return render_template("milk/summary_traditional.html", data=traditional_data, fy=fy)

@milk_bp.route("/test")
def test_route():
    return "Milk module is working!"

@milk_bp.route("/parties/add", methods=["POST"])
def add_party():
    """Add a new party via AJAX"""
    try:
        cid = session.get("company_id", 1)
        name = request.form.get("name", "").strip()
        
        if not name:
            return jsonify({"success": False, "message": "Party name is required"})
        
        # Check if party already exists (case-insensitive)
        existing = Party.query.filter(
            Party.company_id == cid,
            db.func.lower(Party.name) == name.lower()
        ).first()
        if existing:
            return jsonify({"success": False, "message": f"Party '{name}' already exists. Please use a different name."})
        
        party = Party(
            company_id=cid,
            name=name,
            phone=request.form.get("phone"),
            email=request.form.get("email"),
            gstin=request.form.get("gst_number"),
            address=request.form.get("address"),
            state_code=request.form.get("state_code"),
            is_active=True
        )
        
        db.session.add(party)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "id": party.id,
            "name": party.name,
            "message": "Party added successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        })

@milk_bp.route("/milk/entry/<int:txn_id>/delete", methods=["POST"])
@login_required
def delete_entry(txn_id):
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Get the milk transaction
    txn = MilkTransaction.query.filter_by(id=txn_id, company_id=cid, fin_year=fy).first()
    if not txn:
        flash("Milk entry not found", "error")
        return redirect(url_for('milk.entry_list'))
    
    try:
        # Delete associated bill if exists
        if txn.bill_id:
            bill = Bill.query.filter_by(id=txn.bill_id).first()
            if bill:
                # Delete bill items first
                BillItem.query.filter_by(bill_id=bill.id).delete()
                db.session.delete(bill)
        
        # Delete the milk transaction
        db.session.delete(txn)
        db.session.commit()
        
        flash("Milk entry deleted successfully", "success")
        return redirect(url_for('milk.entry_list'))
    
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting entry: {str(e)}", "error")
        return redirect(url_for('milk.entry_list'))

@milk_bp.route("/milk/debug/txns")
@login_required
def debug_txns():
    """Simple debug route to inspect saved milk transactions."""
    cid = session.get("company_id")
    fy = session.get("fin_year")
    txns = (MilkTransaction.query
            .filter_by(company_id=cid, fin_year=fy)
            .order_by(MilkTransaction.id)
            .all())

    lines = []
    for t in txns:
        party_name = t.party.name if getattr(t, "party", None) else "-"
        lines.append(
            f"ID={t.id} date={t.txn_date} party={party_name} qty={t.qty_liters} "
            f"fat={t.fat} snf={t.snf} rate={t.rate} amount={t.amount}"
        )

    return "<pre>" + "\n".join(lines) + "</pre>"
