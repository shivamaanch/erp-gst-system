from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify
from flask_login import login_required
from extensions import db
from models import MilkRateChart, MilkTransaction, Party, Bill, BillItem
from datetime import date, datetime
from sqlalchemy import text

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

@milk_bp.route("/entry", methods=["GET"])
def entry_list():
    # Initialize session if not set
    if not session.get("company_id"):
        session["company_id"] = 1
        session["company_name"] = "Default Company"
        session["fin_year"] = "2025-26"
        session["user_role"] = "admin"
    
    cid = session.get("company_id"); fy = session.get("fin_year")
    
    # Check if bill_id column exists in milk_transactions
    try:
        db.session.execute(text("SELECT bill_id FROM milk_transactions LIMIT 1"))
        # If bill_id exists, use the full query
        sql = """
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.party_id, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.rate, t.amount, t.chart_id, t.narration,
               t.bill_id, p.name as party_name, b.bill_no
        FROM milk_transactions t
        LEFT JOIN parties p ON t.party_id = p.id
        LEFT JOIN bills b ON t.bill_id = b.id
        WHERE t.company_id = :company_id AND t.fin_year = :fin_year 
        ORDER BY t.txn_date DESC 
        LIMIT 200
        """
    except Exception:
        # If bill_id doesn't exist, use query without it
        sql = """
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.party_id, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.rate, t.amount, t.chart_id, t.narration,
               NULL as bill_id, p.name as party_name, NULL as bill_no
        FROM milk_transactions t
        LEFT JOIN parties p ON t.party_id = p.id
        WHERE t.company_id = :company_id AND t.fin_year = :fin_year 
        ORDER BY t.txn_date DESC 
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
                # Add party object for template compatibility
                class SimpleParty:
                    def __init__(self, name, id):
                        self.name = name
                        self.id = id
                self.party = SimpleParty(row.party_name, row.party_id) if row.party_name else None
                # Convert string date to datetime object for strftime compatibility
                from datetime import datetime
                if isinstance(row.txn_date, str):
                    self.txn_date = datetime.strptime(row.txn_date, '%Y-%m-%d').date()
                else:
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
                # Add bill object for template compatibility
                class SimpleBill:
                    def __init__(self, bill_id, bill_no):
                        self.id = bill_id
                        self.bill_no = bill_no
                self.bill = SimpleBill(row.bill_id, row.bill_no) if row.bill_id and row.bill_no else None
        
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
    
    # Add default party if none exist
    if not parties:
        default_party = Party(
            company_id=cid,
            name="Shivam Grover",
            phone="",
            email="",
            address="",
            balance_type="debit",
            opening_balance=0.0,
            is_active=True
        )
        db.session.add(default_party)
        db.session.commit()
        parties = [default_party]
    
    return render_template("milk/entry_list_traditional.html", 
                     txns=txns, total_qty=total_qty, total_amt=total_amt,
                     avg_fat=avg_fat, avg_snf=avg_snf,
                     total_bf_kgs=total_bf_kgs, total_snf_kgs=total_snf_kgs,
                     parties=parties)

@milk_bp.route("/milk/purchase-list")
@login_required
def purchase_list():
    # Initialize session if not set
    if not session.get("company_id"):
        session["company_id"] = 1
        session["company_name"] = "Default Company"
        session["fin_year"] = "2025-26"
        session["user_role"] = "admin"
    
    cid = session.get("company_id"); fy = session.get("fin_year")
    
    # Check if bill_id column exists in milk_transactions
    try:
        db.session.execute(text("SELECT bill_id FROM milk_transactions LIMIT 1"))
        # If bill_id exists, use the full query
        sql = """
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.party_id, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.rate, t.amount, t.chart_id, t.narration,
               t.bill_id, p.name as party_name, b.bill_no
        FROM milk_transactions t
        LEFT JOIN parties p ON t.party_id = p.id
        LEFT JOIN bills b ON t.bill_id = b.id
        WHERE t.company_id = :company_id AND t.fin_year = :fin_year AND t.txn_type = 'Purchase'
        ORDER BY t.txn_date DESC 
        LIMIT 200
        """
    except Exception:
        # If bill_id doesn't exist, use query without it
        sql = """
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.party_id, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.rate, t.amount, t.chart_id, t.narration,
               NULL as bill_id, p.name as party_name, NULL as bill_no
        FROM milk_transactions t
        LEFT JOIN parties p ON t.party_id = p.id
        WHERE t.company_id = :company_id AND t.fin_year = :fin_year AND t.txn_type = 'Purchase'
        ORDER BY t.txn_date DESC 
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
                # Add party object for template compatibility
                class SimpleParty:
                    def __init__(self, name, id):
                        self.name = name
                        self.id = id
                self.party = SimpleParty(row.party_name, row.party_id) if row.party_name else None
                # Convert string date to datetime object for strftime compatibility
                from datetime import datetime
                if isinstance(row.txn_date, str):
                    self.txn_date = datetime.strptime(row.txn_date, '%Y-%m-%d').date()
                else:
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
                # Add bill object for template compatibility
                class SimpleBill:
                    def __init__(self, bill_id, bill_no):
                        self.id = bill_id
                        self.bill_no = bill_no
                self.bill = SimpleBill(row.bill_id, row.bill_no) if row.bill_id and row.bill_no else None
        
        txns.append(SimpleMilkTransaction(row))
    
    # Calculate totals for Purchase only
    total_qty = sum(float(t.qty_liters) for t in txns)
    total_amt = sum(float(t.amount) for t in txns)
    avg_fat = sum(t.fat for t in txns) / len(txns) if txns else 0
    avg_snf = sum(t.snf for t in txns) / len(txns) if txns else 0
    total_bf_kgs = sum(t.qty_liters * t.fat / 100 for t in txns)
    total_snf_kgs = sum(t.qty_liters * t.snf / 100 for t in txns)
    
    # Get parties for filter dropdown
    parties = Party.query.filter_by(company_id=cid, is_active=True).order_by(Party.name).all()
    
    return render_template("milk/purchase_list.html", 
                     txns=txns, total_qty=total_qty, total_amt=total_amt,
                     avg_fat=avg_fat, avg_snf=avg_snf,
                     total_bf_kgs=total_bf_kgs, total_snf_kgs=total_snf_kgs,
                     parties=parties)

@milk_bp.route("/milk/sale-list")
@login_required
def sale_list():
    # Initialize session if not set
    if not session.get("company_id"):
        session["company_id"] = 1
        session["company_name"] = "Default Company"
        session["fin_year"] = "2025-26"
        session["user_role"] = "admin"
    
    cid = session.get("company_id"); fy = session.get("fin_year")
    
    # Check if bill_id column exists in milk_transactions
    try:
        db.session.execute(text("SELECT bill_id FROM milk_transactions LIMIT 1"))
        # If bill_id exists, use the full query
        sql = """
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.party_id, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.rate, t.amount, t.chart_id, t.narration,
               t.bill_id, p.name as party_name, b.bill_no
        FROM milk_transactions t
        LEFT JOIN parties p ON t.party_id = p.id
        LEFT JOIN bills b ON t.bill_id = b.id
        WHERE t.company_id = :company_id AND t.fin_year = :fin_year AND t.txn_type = 'Sale'
        ORDER BY t.txn_date DESC 
        LIMIT 200
        """
    except Exception:
        # If bill_id doesn't exist, use query without it
        sql = """
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.party_id, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.rate, t.amount, t.chart_id, t.narration,
               NULL as bill_id, p.name as party_name, NULL as bill_no
        FROM milk_transactions t
        LEFT JOIN parties p ON t.party_id = p.id
        WHERE t.company_id = :company_id AND t.fin_year = :fin_year AND t.txn_type = 'Sale'
        ORDER BY t.txn_date DESC 
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
                # Add party object for template compatibility
                class SimpleParty:
                    def __init__(self, name, id):
                        self.name = name
                        self.id = id
                self.party = SimpleParty(row.party_name, row.party_id) if row.party_name else None
                # Convert string date to datetime object for strftime compatibility
                from datetime import datetime
                if isinstance(row.txn_date, str):
                    self.txn_date = datetime.strptime(row.txn_date, '%Y-%m-%d').date()
                else:
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
                # Add bill object for template compatibility
                class SimpleBill:
                    def __init__(self, bill_id, bill_no):
                        self.id = bill_id
                        self.bill_no = bill_no
                self.bill = SimpleBill(row.bill_id, row.bill_no) if row.bill_id and row.bill_no else None
        
        txns.append(SimpleMilkTransaction(row))
    
    # Calculate totals for Sale only
    total_qty = sum(float(t.qty_liters) for t in txns)
    total_amt = sum(float(t.amount) for t in txns)
    avg_fat = sum(t.fat for t in txns) / len(txns) if txns else 0
    avg_snf = sum(t.snf for t in txns) / len(txns) if txns else 0
    total_bf_kgs = sum(t.qty_liters * t.fat / 100 for t in txns)
    total_snf_kgs = sum(t.qty_liters * t.snf / 100 for t in txns)
    
    # Get parties for filter dropdown
    parties = Party.query.filter_by(company_id=cid, is_active=True).order_by(Party.name).all()
    
    return render_template("milk/sale_list.html", 
                     txns=txns, total_qty=total_qty, total_amt=total_amt,
                     avg_fat=avg_fat, avg_snf=avg_snf,
                     total_bf_kgs=total_bf_kgs, total_snf_kgs=total_snf_kgs,
                     parties=parties)

@milk_bp.route("/milk/milk-statement")
@login_required
def milk_statement():
    # Initialize session if not set
    if not session.get("company_id"):
        session["company_id"] = 1
        session["company_name"] = "Default Company"
        session["fin_year"] = "2025-26"
        session["user_role"] = "admin"
    
    cid = session.get("company_id"); fy = session.get("fin_year")
    
    # Check if bill_id column exists in milk_transactions
    try:
        db.session.execute(text("SELECT bill_id FROM milk_transactions LIMIT 1"))
        # If bill_id exists, use the full query
        sql = """
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.party_id, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.rate, t.amount, t.chart_id, t.narration,
               t.bill_id, p.name as party_name, b.bill_no
        FROM milk_transactions t
        LEFT JOIN parties p ON t.party_id = p.id
        LEFT JOIN bills b ON t.bill_id = b.id
        WHERE t.company_id = :company_id AND t.fin_year = :fin_year 
        ORDER BY t.txn_date DESC 
        LIMIT 500
        """
    except Exception:
        # If bill_id doesn't exist, use query without it
        sql = """
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.party_id, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.rate, t.amount, t.chart_id, t.narration,
               NULL as bill_id, p.name as party_name, NULL as bill_no
        FROM milk_transactions t
        LEFT JOIN parties p ON t.party_id = p.id
        WHERE t.company_id = :company_id AND t.fin_year = :fin_year 
        ORDER BY t.txn_date DESC 
        LIMIT 500
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
                # Add party object for template compatibility
                class SimpleParty:
                    def __init__(self, name, id):
                        self.name = name
                        self.id = id
                self.party = SimpleParty(row.party_name, row.party_id) if row.party_name else None
                # Convert string date to datetime object for strftime compatibility
                from datetime import datetime
                if isinstance(row.txn_date, str):
                    self.txn_date = datetime.strptime(row.txn_date, '%Y-%m-%d').date()
                else:
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
                # Add bill object for template compatibility
                class SimpleBill:
                    def __init__(self, bill_id, bill_no):
                        self.id = bill_id
                        self.bill_no = bill_no
                self.bill = SimpleBill(row.bill_id, row.bill_no) if row.bill_id and row.bill_no else None
        
        txns.append(SimpleMilkTransaction(row))
    
    # Calculate totals for Purchase only
    purchase_txns = [t for t in txns if t.txn_type == 'Purchase']
    purchase_total_qty = sum(float(t.qty_liters) for t in purchase_txns)
    purchase_total_amt = sum(float(t.amount) for t in purchase_txns)
    purchase_avg_fat = sum(t.fat for t in purchase_txns) / len(purchase_txns) if purchase_txns else 0
    purchase_avg_snf = sum(t.snf for t in purchase_txns) / len(purchase_txns) if purchase_txns else 0
    purchase_total_bf_kgs = sum(t.qty_liters * t.fat / 100 for t in purchase_txns)
    purchase_total_snf_kgs = sum(t.qty_liters * t.snf / 100 for t in purchase_txns)
    
    # Calculate totals for Sale only
    sale_txns = [t for t in txns if t.txn_type == 'Sale']
    sale_total_qty = sum(float(t.qty_liters) for t in sale_txns)
    sale_total_amt = sum(float(t.amount) for t in sale_txns)
    sale_avg_fat = sum(t.fat for t in sale_txns) / len(sale_txns) if sale_txns else 0
    sale_avg_snf = sum(t.snf for t in sale_txns) / len(sale_txns) if sale_txns else 0
    sale_total_bf_kgs = sum(t.qty_liters * t.fat / 100 for t in sale_txns)
    sale_total_snf_kgs = sum(t.qty_liters * t.snf / 100 for t in sale_txns)
    
    # Get parties for filter dropdown
    parties = Party.query.filter_by(company_id=cid, is_active=True).order_by(Party.name).all()
    
    return render_template("milk/milk_statement.html", 
                     txns=txns,
                     purchase_total_qty=purchase_total_qty, purchase_total_amount=purchase_total_amt,
                     purchase_avg_fat=purchase_avg_fat, purchase_avg_snf=purchase_avg_snf,
                     purchase_total_bf_kgs=purchase_total_bf_kgs, purchase_total_snf_kgs=purchase_total_snf_kgs,
                     sale_total_qty=sale_total_qty, sale_total_amount=sale_total_amt,
                     sale_avg_fat=sale_avg_fat, sale_avg_snf=sale_avg_snf,
                     sale_total_bf_kgs=sale_total_bf_kgs, sale_total_snf_kgs=sale_total_snf_kgs,
                     parties=parties)

@milk_bp.route("/entry/add", methods=["GET","POST"])
def add_entry():
    # Initialize session if not set
    if not session.get("company_id"):
        session["company_id"] = 1
        session["company_name"] = "Default Company"
        session["fin_year"] = "2025-26"
        session["user_role"] = "admin"
    
    cid = session.get("company_id"); fy = session.get("fin_year")
    parties = Party.query.filter_by(company_id=cid, is_active=True).order_by(Party.name).all()
    
    # Add default party if none exist
    if not parties:
        default_party = Party(
            company_id=cid,
            name="Shivam Grover",
            phone="",
            email="",
            address="",
            balance_type="debit",
            opening_balance=0.0,
            is_active=True
        )
        db.session.add(default_party)
        db.session.commit()
        parties = [default_party]
    
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
        print(f"DEBUG: Received amount_str={amount_str}, calc_rate_str={calc_rate_str}")
        if amount_str:
            amount = float(amount_str)
            if calc_rate_str:
                rate = float(calc_rate_str)
            else:
                rate = round(amount / qty, 4) if qty else 0
            print(f"DEBUG: Using frontend amount={amount}, rate={rate}")
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
        print(f"DEBUG: create_invoice = {create_invoice}")
        print(f"DEBUG: form data = {dict(request.form)}")
        
        txn=MilkTransaction(company_id=cid,fin_year=fy,party_id=party_id,txn_date=txn_date,
            shift=request.form.get("shift","Morning"),txn_type=txn_type,
            qty_liters=qty,fat=fat,snf=snf,clr=float(request.form.get("clr",0)),rate=rate,amount=amount,
            chart_id=chart_id,narration=request.form.get("narration","").strip())
        db.session.add(txn)
        db.session.flush()  # Get the transaction ID
        bill_no=None
        if create_invoice:
            print(f"DEBUG: Creating invoice for transaction {txn.id}")
            print(f"DEBUG: create_invoice = {create_invoice}")
            print(f"DEBUG: form data = {dict(request.form)}")
            
            bill_type="Sales" if txn_type=="Sale" else "Purchase"
            print(f"DEBUG: bill_type = {bill_type}")
            
            # Use manual invoice number if provided, otherwise generate automatic
            manual_bill_no = request.form.get("manual_bill_no", "").strip()
            print(f"DEBUG: manual_bill_no = '{manual_bill_no}'")
            
            if manual_bill_no:
                bill_no = manual_bill_no
                print(f"DEBUG: Using manual bill number: {bill_no}")
            else:
                # Generate bill number in P/0001/25-26 format
                print(f"DEBUG: Generating automatic bill number...")
                last_bill = Bill.query.filter_by(company_id=cid, bill_type=bill_type).order_by(Bill.id.desc()).first()
                next_num = (last_bill.id + 1) if last_bill else 1
                prefix = "P" if bill_type == "Purchase" else "S"
                bill_no = f"{prefix}/{str(next_num).zfill(4)}/{fy}"
                print(f"DEBUG: Generated bill number: {bill_no}")
            
            gst_rate=float(request.form.get("gst_rate") or 0)
            gst_amt=round(amount*gst_rate/100,2); total=round(amount+gst_amt,2)
            print(f"DEBUG: GST rate: {gst_rate}, GST amount: {gst_amt}, Total: {total}")
            
            bill=Bill(company_id=cid,fin_year=fy,party_id=party_id,bill_no=bill_no,
                bill_date=txn_date,bill_type=bill_type,taxable_amount=amount,
                cgst=gst_amt/2, sgst=gst_amt/2, igst=0, total_amount=total,
                narration=f"Milk {txn_type} | FAT:{fat}% SNF:{snf}% | {qty}L @ Rs{rate}/L",
                is_cancelled=False)
            print(f"DEBUG: Creating bill object...")
            db.session.add(bill)
            print(f"DEBUG: Flushing session to get bill ID...")
            db.session.flush()
            print(f"DEBUG: Bill created with ID: {bill.id}")
            
            # Always create a BillItem for the milk invoice
            item=BillItem(bill_id=bill.id,qty=qty,rate=rate,taxable_amount=amount,
                gst_rate=gst_rate,cgst=gst_amt/2,sgst=gst_amt/2,igst=0)
            print(f"DEBUG: Creating bill item...")
            db.session.add(item)
            print(f"DEBUG: Setting txn.bill_id = {bill.id}")
            try:
                txn.bill_id = bill.id
            except Exception as e:
                print(f"WARNING: Could not set bill_id (column may not exist): {e}")
            print(f"DEBUG: Invoice creation completed")
            db.session.commit()
            msg=f"Saved {qty}L @ Rs{rate}/L = Rs{amount}"
            if bill_no: msg+=f" | Invoice {bill_no} created"
            flash(msg,"success")
            return redirect(url_for("milk.entry_list"))
        
    return render_template("milk/entry_form_traditional.html", parties=parties, charts=charts, today=date.today().isoformat(), edit_mode=False)

@milk_bp.route("/entry/<int:txn_id>/edit", methods=["GET","POST"])
def edit_entry(txn_id):
    cid     = session.get("company_id"); fy = session.get("fin_year")
    
    # Initialize session if not set
    if not cid:
        session["company_id"] = 1
        session["company_name"] = "Default Company"
        session["fin_year"] = "2025-26"
        session["user_role"] = "admin"
        cid = 1; fy = "2025-26"
    
    # Add CLR column if it doesn't exist
    try:
        from sqlalchemy import text
        check_sql = "SELECT clr FROM milk_transactions LIMIT 1"
        db.session.execute(text(check_sql))
        print("DEBUG: CLR column already exists")
    except Exception as e:
        print(f"DEBUG: CLR column missing, adding it: {e}")
        try:
            alter_sql = "ALTER TABLE milk_transactions ADD COLUMN clr REAL DEFAULT 0.0"
            db.session.execute(text(alter_sql))
            db.session.commit()
            print("DEBUG: CLR column added successfully")
        except Exception as e2:
            print(f"DEBUG: Error adding CLR column: {e2}")
            db.session.rollback()
    
    parties = Party.query.filter_by(company_id=cid, is_active=True).order_by(Party.name).all()
    
    # Add default party if none exist
    if not parties:
        default_party = Party(
            company_id=cid,
            name="Shivam Grover",
            phone="",
            email="",
            address="",
            balance_type="debit",
            opening_balance=0.0,
            is_active=True
        )
        db.session.add(default_party)
        db.session.commit()
        parties = [default_party]
    
    charts  = MilkRateChart.query.filter_by(company_id=cid, is_active=True).order_by(MilkRateChart.effective_date.desc()).all()
    
    # Get existing transaction - use raw SQL to avoid ORM issues
    from sqlalchemy import text
    sql = """
    SELECT id, company_id, fin_year, voucher_no, party_id, txn_date, shift, 
           txn_type, qty_liters, fat, snf, clr, rate, amount, chart_id, narration, bill_id
    FROM milk_transactions 
    WHERE id = :txn_id AND company_id = :company_id AND fin_year = :fin_year
    """
    result = db.session.execute(text(sql), {"txn_id": txn_id, "company_id": cid, "fin_year": fy})
    row = result.fetchone()
    
    if not row:
        print(f"DEBUG: Transaction {txn_id} not found in database!")
        # If transaction not found, create a dummy one for testing
        class DummyTransaction:
            def __init__(self):
                self.id = txn_id
                self.company_id = cid
                self.fin_year = fy
                self.voucher_no = f"V{txn_id:04d}"
                self.party_id = 1
                self.txn_date = datetime.now().date()
                self.shift = "Morning"
                self.txn_type = "Purchase"
                self.qty_liters = 8.0
                self.fat = 2.0
                self.snf = 8.5
                self.clr = 0.0
                self.rate = 22.79
                self.amount = 182.34
                self.chart_id = None
                self.narration = "Test transaction"
                self.bill_id = None
        
        txn = DummyTransaction()
    else:
        print(f"DEBUG: Found transaction in database:")
        print(f"  ID: {row.id}, FAT: {row.fat}, SNF: {row.snf}, CLR: {getattr(row, 'clr', 'N/A')}, RATE: {row.rate}, AMOUNT: {row.amount}")
        
        # Get party information for this transaction
        party = Party.query.filter_by(id=row.party_id).first()
        party_name = party.name if party else "Unknown Party"
        print(f"  Party: {party_name} (ID: {row.party_id})")

        # Get associated bill (if any) so we can show / edit invoice number
        bill = None
        bill_no = None
        if getattr(row, 'bill_id', None):
            bill = Bill.query.filter_by(id=row.bill_id, company_id=cid).first()
            bill_no = bill.bill_no if bill else None
            print(f"  Bill: {bill_no} (ID: {row.bill_id})")
        
        # Create a simple object with the data
        class SimpleMilkTransaction:
            def __init__(self, row):
                self.id = row.id
                self.company_id = row.company_id
                self.fin_year = row.fin_year
                self.voucher_no = row.voucher_no
                self.party_id = row.party_id
                # Add party object for template compatibility
                class SimpleParty:
                    def __init__(self, name, id):
                        self.name = name
                        self.id = id
                self.party = SimpleParty(party_name, row.party_id)
                # Convert string date to datetime object for strftime compatibility
                from datetime import datetime
                if isinstance(row.txn_date, str):
                    self.txn_date = datetime.strptime(row.txn_date, '%Y-%m-%d').date()
                else:
                    self.txn_date = row.txn_date
                self.shift = row.shift
                self.txn_type = row.txn_type
                self.qty_liters = row.qty_liters
                self.fat = row.fat
                self.snf = row.snf
                # Use actual CLR value if available, otherwise 0.0
                self.clr = getattr(row, 'clr', 0.0)
                self.rate = row.rate
                self.amount = row.amount
                self.chart_id = row.chart_id
                self.narration = row.narration
                # Attach bill information for template (if any)
                self.bill_id = getattr(row, 'bill_id', None)
                class SimpleBill:
                    def __init__(self, id, bill_no):
                        self.id = id
                        self.bill_no = bill_no
                self.bill = SimpleBill(self.bill_id, bill_no) if bill_no else None
        
        txn = SimpleMilkTransaction(row)
    
    if request.method == "POST":
        print("DEBUG: POST request received - updating transaction")
        print(f"DEBUG: Form data received: {dict(request.form)}")
        
        # Get the actual database transaction to update
        actual_txn = MilkTransaction.query.filter_by(id=txn_id, company_id=cid, fin_year=fy).first()
        if not actual_txn:
            print(f"DEBUG: Could not find actual transaction {txn_id} to update!")
            flash("Transaction not found for update", "error")
            return redirect(url_for("milk.entry_list"))
        
        print(f"DEBUG: Found actual transaction {actual_txn.id} to update")
        print(f"DEBUG: Before update - FAT: {actual_txn.fat}, SNF: {actual_txn.snf}, RATE: {actual_txn.rate}, AMOUNT: {actual_txn.amount}")
        
        # Update the actual database transaction
        actual_txn.txn_date = datetime.strptime(request.form["txn_date"], "%Y-%m-%d").date()
        actual_txn.shift = request.form["shift"]
        actual_txn.txn_type = request.form["txn_type"]
        actual_txn.party_id = int(request.form["party_id"])
        actual_txn.qty_liters = float(request.form["qty_liters"])
        actual_txn.fat = float(request.form["fat"])
        actual_txn.clr = float(request.form.get("clr", 0.0))  # CLR might not exist in DB
        actual_txn.snf = float(request.form.get("snf_auto", 8.5))

        # Traditional Indian Milk Pricing Method (SNF Method)
        daily_rate_str = (request.form.get("rate_per_liter") or "").strip()
        amount_str = (request.form.get("amount") or "").strip()
        
        if daily_rate_str and daily_rate_str != '0':
            daily_rate = float(daily_rate_str)
            print(f"DEBUG: Using traditional method with daily rate: {daily_rate}")
            
            # Traditional 60:40 split between fat and SNF
            fat_share = 0.60
            snf_share = 0.40
            std_fat_kg = 6.5
            std_snf_kg = 8.5
            
            # Calculate component rates (traditional method)
            ghee_rate = (daily_rate * fat_share) / std_fat_kg  # ≈ ₹415/kg
            powder_rate = (daily_rate * snf_share) / std_snf_kg # ≈ ₹211/kg
            
            # Calculate component amounts
            qty = actual_txn.qty_liters
            fat = actual_txn.fat
            clr = actual_txn.clr
            
            # Calculate SNF using Richmond's formula (same as frontend)
            if clr > 0:
                calculated_snf = (clr / 4) + (0.20 * fat) + 0.14
                calculated_snf = max(7.0, min(15.0, calculated_snf))
            else:
                calculated_snf = 7.54
            
            bf_kgs = qty * fat / 100
            snf_kgs = qty * calculated_snf / 100
            
            print(f"DEBUG: Using calculated SNF: {calculated_snf:.2f} (stored SNF: {actual_txn.snf:.2f})")
            
            ghee_amount = bf_kgs * ghee_rate
            powder_amount = snf_kgs * powder_rate
            final_amount = ghee_amount + powder_amount

            actual_txn.rate = round(final_amount / qty, 4) if qty else 0
            actual_txn.amount = final_amount
            
            print(f"DEBUG: Traditional calculation:")
            print(f"  Ghee: {bf_kgs:.3f}kg × ₹{ghee_rate:.2f} = ₹{ghee_amount:.2f}")
            print(f"  Powder: {snf_kgs:.3f}kg × ₹{powder_rate:.2f} = ₹{powder_amount:.2f}")
            print(f"  Total: ₹{final_amount:.2f}")
            
        elif amount_str:
            actual_txn.amount = float(amount_str)
            print(f"DEBUG: Using provided amount: {actual_txn.amount}")
        else:
            actual_txn.amount = 0.0
            print(f"DEBUG: No rate or amount provided")
        actual_txn.narration = request.form.get("narration", "").strip()
        
        # Handle invoice creation/update
        create_invoice = request.form.get("create_invoice") == "on"
        manual_bill_no = (request.form.get("manual_bill_no") or "").strip()

        if actual_txn.bill_id:
            # Update existing invoice number if user provided one
            bill = Bill.query.filter_by(id=actual_txn.bill_id, company_id=cid).first()
            if bill and manual_bill_no:
                print(f"DEBUG: Updating existing bill {bill.id} number to {manual_bill_no}")
                bill.bill_no = manual_bill_no
        elif create_invoice:
            # Create new invoice (only if one doesn't already exist)
            bill_type="Sales" if actual_txn.txn_type=="Sale" else "Purchase"
            # Use manual invoice number if provided, otherwise generate automatic
            if manual_bill_no:
                bill_no = manual_bill_no
            else:
                # Generate bill number in P/0001/25-26 format
                last_bill = Bill.query.filter_by(company_id=cid, bill_type=bill_type).order_by(Bill.id.desc()).first()
                next_num = (last_bill.id + 1) if last_bill else 1
                prefix = "P" if bill_type == "Purchase" else "S"
                bill_no = f"{prefix}/{str(next_num).zfill(4)}/{fy}"
            gst_rate=float(request.form.get("gst_rate") or 0)
            gst_amt=round(actual_txn.amount*gst_rate/100,2); total=round(actual_txn.amount+gst_amt,2)
            bill=Bill(company_id=cid,fin_year=fy,party_id=actual_txn.party_id,bill_no=bill_no,
                bill_date=actual_txn.txn_date,bill_type=bill_type,taxable_amount=actual_txn.amount,
                cgst=gst_amt/2, sgst=gst_amt/2, igst=0, total_amount=total,
                narration=actual_txn.narration, is_cancelled=False)
            db.session.add(bill); db.session.flush()
            item=BillItem(bill_id=bill.id,qty=actual_txn.qty_liters,rate=actual_txn.rate,taxable_amount=actual_txn.amount,
                gst_rate=gst_rate,cgst=gst_amt/2,sgst=gst_amt/2,igst=0)
            db.session.add(item); actual_txn.bill_id=bill.id
        
        print("DEBUG: Committing to database...")
        db.session.commit()
        print(f"DEBUG: After update - FAT: {actual_txn.fat}, SNF: {actual_txn.snf}, RATE: {actual_txn.rate}, AMOUNT: {actual_txn.amount}")
        print("DEBUG: Database commit successful!")
        flash(f"Milk entry updated successfully", "success")
        return redirect(url_for("milk.entry_list"))
    
    # Pre-fill form with existing data
    return render_template("milk/entry_form_traditional.html", 
                     parties=parties, charts=charts, 
                     txn=txn, edit_mode=True,
                     today=txn.txn_date.isoformat())

@milk_bp.route("/entry/<int:txn_id>/update-field", methods=["POST"])
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

@milk_bp.route("/entry/<int:txn_id>/delete", methods=["POST"])
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

@milk_bp.route("/milk/debug/routes")
def debug_routes():
    """Debug route to check if blueprint is working"""
    print("DEBUG: debug_routes called - blueprint is working!")
    return "Milk blueprint is working! Routes are registered."

@milk_bp.route("/milk/debug/txns")
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
