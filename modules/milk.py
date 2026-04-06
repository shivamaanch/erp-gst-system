from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify
from flask_login import login_required
from extensions import db
from models import MilkRateChart, MilkTransaction, Account, Bill, BillItem, JournalHeader, JournalLine, Party
from datetime import date, datetime, timedelta
from sqlalchemy import text
from decimal import Decimal, ROUND_HALF_UP

# Safe database execution wrapper to handle transaction errors
def safe_db_execute(sql, params=None):
    """Execute database query with transaction error handling"""
    try:
        # Clear any existing failed transactions
        db.session.rollback()
        # Execute the query
        result = db.session.execute(text(sql), params or {})
        return result
    except Exception as e:
        # Force rollback and remove session
        try:
            db.session.rollback()
            db.session.remove()
        except:
            pass
        # Try once more with fresh session
        result = db.session.execute(text(sql), params or {})
        return result

def to_int_or_none(val):
    """Convert form value to integer or None if empty/invalid"""
    try:
        return int(val) if val and str(val).strip() else None
    except (ValueError, TypeError):
        return None

milk_bp = Blueprint("milk", __name__)

def calc_rate(fat, snf, fat_rate, snf_rate):
    return round(float(fat)*float(fat_rate) + float(snf)*float(snf_rate), 4)


def _round2(value):
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _round3(value):
    return float(Decimal(str(value)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))


def compute_snf(clr, fat):
    """Richmond formula with proper CLR truncation; cap at 15."""
    import math
    # Truncate CLR/4 to 2 decimal places (no rounding)
    clr_div_truncated = math.floor((float(clr) / 4.0) * 100) / 100
    snf = clr_div_truncated + (0.20 * float(fat)) + 0.14
    snf = min(15.0, snf)
    return snf


def compute_component_breakdown(qty, fat, snf, daily_rate):
    """Single source of truth for milk amount calculation."""
    qty = float(qty)
    fat = float(fat)
    snf = float(snf)
    daily_rate = float(daily_rate)

    fat_share = 0.60
    snf_share = 0.40
    std_fat_kg = 6.5
    std_snf_kg = 8.5

    # Calculate component rates (full precision)
    bf_rate_raw = (daily_rate * fat_share) / std_fat_kg
    snf_rate_raw = (daily_rate * snf_share) / std_snf_kg

    # Use raw component rates and kgs for calculation
    bf_rate_used = bf_rate_raw
    snf_rate_used = snf_rate_raw

    bf_kgs_raw = (qty * fat) / 100.0
    snf_kgs_raw = (qty * snf) / 100.0

    # Compute component amounts with full precision; round only final display values
    bf_amount_raw = bf_kgs_raw * bf_rate_used
    snf_amount_raw = snf_kgs_raw * snf_rate_used
    amount_raw = bf_amount_raw + snf_amount_raw

    bf_amount = _round2(bf_amount_raw)
    snf_amount = _round2(snf_amount_raw)
    amount = _round2(amount_raw)

    return {
        "bf_rate": bf_rate_raw,
        "snf_rate": snf_rate_raw,
        "bf_kgs": bf_kgs_raw,
        "snf_kgs": snf_kgs_raw,
        "bf_rate_display": bf_rate_used,
        "snf_rate_display": snf_rate_used,
        "bf_kgs_display": bf_kgs_raw,
        "snf_kgs_display": snf_kgs_raw,
        "bf_amount": bf_amount,
        "snf_amount": snf_amount,
        "amount": amount,
        "bf_amount_raw": bf_amount_raw,
        "snf_amount_raw": snf_amount_raw,
        "amount_raw": amount_raw,
    }

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
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.clr, t.rate, t.amount, t.chart_id, t.narration,
               t.bill_id, 'Unknown' as account_name, b.bill_no
        FROM milk_transactions t
        LEFT JOIN bills b ON t.bill_id = b.id
        WHERE t.company_id = :company_id AND t.fin_year = :fin_year 
        ORDER BY t.txn_date DESC 
        LIMIT 200
        """
    except Exception:
        # If bill_id doesn't exist, use query without it
        sql = """
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.clr, t.rate, t.amount, t.chart_id, t.narration,
               NULL as bill_id, 'Unknown' as account_name, NULL as bill_no
        FROM milk_transactions t
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
                self.account_id = getattr(row, 'account_id', None)
                # Add account object for template compatibility
                class SimpleAccount:
                    def __init__(self, name, id):
                        self.name = name
                        self.id = id
                
                # Extract party name from narration
                party_name = "Unknown"
                if row.narration and "Party:" in row.narration:
                    # Extract party name from "Mobile Purchase | Party: Party Name | ..."
                    parts = row.narration.split("|")
                    for part in parts:
                        if "Party:" in part:
                            party_name = part.split("Party:")[1].strip()
                            break
                elif row.account_name and row.account_name != "Unknown":
                    party_name = row.account_name
                
                self.account = SimpleAccount(party_name, getattr(row, 'account_id', None))
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
                self.clr = row.clr
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
            balance_type="Dr",
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
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.clr, t.rate, t.amount, t.chart_id, t.narration,
               t.bill_id, 'Unknown' as account_name, b.bill_no
        FROM milk_transactions t
        LEFT JOIN bills b ON t.bill_id = b.id
        WHERE t.company_id = :company_id AND t.fin_year = :fin_year AND t.txn_type = 'Purchase'
        ORDER BY t.txn_date DESC 
        LIMIT 200
        """
    except Exception:
        # If bill_id doesn't exist, use query without it
        sql = """
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.clr, t.rate, t.amount, t.chart_id, t.narration,
               NULL as bill_id, 'Unknown' as account_name, NULL as bill_no
        FROM milk_transactions t
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
                self.account_id = getattr(row, 'account_id', None)
                # Add account object for template compatibility
                class SimpleAccount:
                    def __init__(self, name, id):
                        self.name = name
                        self.id = id
                self.account = SimpleAccount(row.account_name or "Cash Account", getattr(row, 'account_id', None)) if row.account_name else None
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
                self.clr = row.clr
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
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.clr, t.rate, t.amount, t.chart_id, t.narration,
               t.bill_id, 
               CASE 
                 WHEN t.narration LIKE '%Party:%' THEN 
                   SUBSTR(t.narration, 
                          INSTR(t.narration, 'Party:') + 6, 
                          CASE 
                            WHEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') > 0 
                            THEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') - 1
                            ELSE LENGTH(t.narration) - INSTR(t.narration, 'Party:') - 5
                          END
                   )
                 ELSE 'Unknown'
               END as account_name, 
               b.bill_no
        FROM milk_transactions t
        LEFT JOIN bills b ON t.bill_id = b.id
        WHERE t.company_id = :company_id AND t.fin_year = :fin_year AND t.txn_type = 'Sale'
        ORDER BY t.txn_date DESC 
        LIMIT 200
        """
    except Exception:
        # If bill_id doesn't exist, use query without it
        sql = """
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.clr, t.rate, t.amount, t.chart_id, t.narration,
               NULL as bill_id, 
               CASE 
                 WHEN t.narration LIKE '%Party:%' THEN 
                   SUBSTR(t.narration, 
                          INSTR(t.narration, 'Party:') + 6, 
                          CASE 
                            WHEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') > 0 
                            THEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') - 1
                            ELSE LENGTH(t.narration) - INSTR(t.narration, 'Party:') - 5
                          END
                   )
                 ELSE 'Unknown'
               END as account_name, 
               NULL as bill_no
        FROM milk_transactions t
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
                self.account_id = getattr(row, 'account_id', None)
                # Add account object for template compatibility
                class SimpleAccount:
                    def __init__(self, name, id):
                        self.name = name
                        self.id = id
                self.account = SimpleAccount(row.account_name or "Cash Account", getattr(row, 'account_id', None)) if row.account_name else None
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
                self.clr = row.clr
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
        # If bill_id exists, use the full query without account_id
        sql = """
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.clr, t.rate, t.amount, t.chart_id, t.narration,
               t.bill_id, 
               CASE 
                 WHEN t.narration LIKE '%Party:%' THEN 
                   SUBSTR(t.narration, 
                          INSTR(t.narration, 'Party:') + 6, 
                          CASE 
                            WHEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') > 0 
                            THEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') - 1
                            ELSE LENGTH(t.narration) - INSTR(t.narration, 'Party:') - 5
                          END
                   )
                 ELSE 'Unknown'
               END as account_name, 
               b.bill_no
        FROM milk_transactions t
        LEFT JOIN bills b ON t.bill_id = b.id
        WHERE t.company_id = :company_id AND t.fin_year = :fin_year 
        ORDER BY t.txn_date DESC 
        LIMIT 500
        """
    except Exception:
        # If bill_id doesn't exist, use query without it
        sql = """
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.clr, t.rate, t.amount, t.chart_id, t.narration,
               NULL as bill_id, 
               CASE 
                 WHEN t.narration LIKE '%Party:%' THEN 
                   SUBSTR(t.narration, 
                          INSTR(t.narration, 'Party:') + 6, 
                          CASE 
                            WHEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') > 0 
                            THEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') - 1
                            ELSE LENGTH(t.narration) - INSTR(t.narration, 'Party:') - 5
                          END
                   )
                 ELSE 'Unknown'
               END as account_name, 
               NULL as bill_no
        FROM milk_transactions t
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
                self.account_id = getattr(row, 'account_id', None)
                # Add account object for template compatibility
                class SimpleAccount:
                    def __init__(self, name, id):
                        self.name = name
                        self.id = id
                
                # Extract party name from narration
                party_name = "Unknown"
                if row.narration and "Party:" in row.narration:
                    # Extract party name from "Mobile Purchase | Party: Party Name | ..."
                    parts = row.narration.split("|")
                    for part in parts:
                        if "Party:" in part:
                            party_name = part.split("Party:")[1].strip()
                            break
                elif row.account_name and row.account_name != "Unknown":
                    party_name = row.account_name
                
                self.account = SimpleAccount(party_name, getattr(row, 'account_id', None))
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
                self.clr = row.clr
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

@milk_bp.route("/milk/import")
@login_required
def milk_import():
    # Initialize session if not set
    if not session.get("company_id"):
        session["company_id"] = 1
        session["company_name"] = "Default Company"
        session["fin_year"] = "2025-26"
        session["user_role"] = "admin"
    
    cid = session.get("company_id"); fy = session.get("fin_year")
    
    # Get filter parameters
    party_search = request.args.get("party_search", "").strip()
    from_date = request.args.get("from_date", "")
    to_date = request.args.get("to_date", "")
    last_10_days = request.args.get("last_10_days") == "1"
    
    # Build base query for milk purchases
    # Use raw SQL to avoid account_id column issues
    sql = """
    SELECT t.id, t.txn_date, t.shift, t.txn_type, t.qty_liters, t.fat, t.snf, t.clr, 
           t.rate, t.amount, t.chart_id, t.narration,
           CASE 
             WHEN t.narration LIKE '%Party:%' THEN 
               SUBSTR(t.narration, 
                      INSTR(t.narration, 'Party:') + 6, 
                      CASE 
                        WHEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') > 0 
                        THEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') - 1
                        ELSE LENGTH(t.narration) - INSTR(t.narration, 'Party:') - 5
                      END
               )
             ELSE 'Unknown'
           END as party_name
    FROM milk_transactions t
    WHERE t.company_id = :company_id AND t.fin_year = :fin_year AND t.txn_type = 'Purchase'
    """
    
    # Apply filters
    params = {"company_id": cid, "fin_year": fy}
    
    if party_search:
        sql += " AND t.narration ILIKE :party_search"
        params["party_search"] = f"%{party_search}%"
    
    if from_date:
        try:
            sql += " AND t.txn_date >= :from_date"
            params["from_date"] = datetime.strptime(from_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    
    if to_date:
        try:
            sql += " AND t.txn_date <= :to_date"
            params["to_date"] = datetime.strptime(to_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    
    if last_10_days:
        ten_days_ago = date.today() - timedelta(days=10)
        sql += " AND t.txn_date >= :last_10_days"
        params["last_10_days"] = ten_days_ago
    
    sql += " ORDER BY t.txn_date DESC"
    
    result = db.session.execute(text(sql), params)
    purchases = result.fetchall()
    
    # Calculate totals
    total_qty = sum(p.qty_liters for p in purchases)
    total_amount = sum(p.amount for p in purchases)
    avg_rate = (total_amount / total_qty) if total_qty > 0 else 0  # This is already per liter
    
    # Prepare data for template
    data = []
    for i, p in enumerate(purchases, 1):
        # Calculate rate per liter for this transaction
        rate_per_liter = p.amount / p.qty_liters if p.qty_liters > 0 else 0
        
        # Get BF and SNF rates from chart if available, otherwise use the same calculation as milk entry
        bf_rate = 0
        snf_rate = 0
        if p.chart_id:
            chart = MilkRateChart.query.get(p.chart_id)
            if chart:
                bf_rate = chart.fat_rate
                snf_rate = chart.snf_rate
        else:
            # Use the same calculation as compute_component_breakdown function
            if p.rate > 0 and p.fat > 0 and p.snf > 0:
                # Use the exact same formula as compute_component_breakdown
                daily_rate = float(p.rate)
                fat_share = 0.60
                snf_share = 0.40
                std_fat_kg = 6.5
                std_snf_kg = 8.5
                
                # Calculate component rates (same as system formula)
                bf_rate_raw = (daily_rate * fat_share) / std_fat_kg
                snf_rate_raw = (daily_rate * snf_share) / std_snf_kg
                
                bf_rate = round(bf_rate_raw, 2)
                snf_rate = round(snf_rate_raw, 2)
            else:
                # Default standard rates
                bf_rate = 200  # Default fat rate
                snf_rate = 100  # Default SNF rate
        
        # Calculate BF kg and SNF kg
        bf_kg = p.qty_liters * p.fat / 100
        snf_kg = p.qty_liters * p.snf / 100
        
        # Extract party name from narration
        supplier_name = "Unknown"
        if p.narration and "Party:" in p.narration:
            # Extract party name from "Mobile Purchase | Party: Party Name | ..."
            parts = p.narration.split("|")
            for part in parts:
                if "Party:" in part:
                    supplier_name = part.split("Party:")[1].strip()
                    break
        elif p.narration:
            # Fallback: if no Party: tag, try to extract from the first part
            first_part = p.narration.split("|")[0].strip()
            # If it's "Mobile Purchase", we don't have a party name, keep "Unknown"
            if not first_part.startswith("Mobile"):
                supplier_name = first_part
        
        # Handle txn_date which might be string or date object
        if isinstance(p.txn_date, str):
            txn_date_str = p.txn_date
        else:
            txn_date_str = p.txn_date.strftime('%d-%m-%Y')
        
        data.append({
            'sr_no': i,
            'date': txn_date_str,
            'supplier': supplier_name,
            'description': f"Qty:{p.qty_liters}L | FAT:{p.fat}% | SNF:{p.snf}% | CLR:{p.clr} | BF:{bf_kg:.2f}kg | SNF:{snf_kg:.2f}kg | BF Rate:{bf_rate} | SNF Rate:{snf_rate} | Rate:{int(p.rate) if p.rate == int(p.rate) else p.rate}",
            'qty': p.qty_liters,
            'rate': rate_per_liter,  # Use calculated rate per liter
            'amount': p.amount
        })
    
    return render_template("milk/milk_import.html", 
                         data=data, 
                         total_qty=total_qty,
                         total_amount=total_amount,
                         avg_rate=avg_rate,
                         party_search=party_search,
                         from_date=from_date,
                         to_date=to_date)

@milk_bp.route("/milk/sale-import")
@login_required
def milk_sale_import():
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Get filters from request
    party_search = request.args.get("party_search", "").strip()
    from_date = request.args.get("from_date", "")
    to_date = request.args.get("to_date", "")
    last_10_days = request.args.get("last_10_days") == "1"
    
    # Build base query for milk sales using raw SQL
    sql = """
    SELECT t.id, t.txn_date, t.qty_liters, t.fat, t.snf, t.clr, 
           t.rate, t.amount, t.chart_id, t.narration,
           CASE 
             WHEN t.narration LIKE '%Party:%' THEN 
               SUBSTR(t.narration, 
                      INSTR(t.narration, 'Party:') + 6, 
                      CASE 
                        WHEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') > 0 
                        THEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') - 1
                        ELSE LENGTH(t.narration) - INSTR(t.narration, 'Party:') - 5
                      END
               )
             ELSE 'Unknown'
           END as party_name
    FROM milk_transactions t
    WHERE t.company_id = :company_id AND t.fin_year = :fin_year AND t.txn_type = 'Sale'
    """
    
    # Apply filters
    params = {"company_id": cid, "fin_year": fy}
    
    if party_search:
        sql += " AND t.narration ILIKE :party_search"
        params["party_search"] = f"%{party_search}%"
    
    if from_date:
        try:
            sql += " AND t.txn_date >= :from_date"
            params["from_date"] = datetime.strptime(from_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    
    if to_date:
        try:
            sql += " AND t.txn_date <= :to_date"
            params["to_date"] = datetime.strptime(to_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    
    if last_10_days:
        ten_days_ago = date.today() - timedelta(days=10)
        sql += " AND t.txn_date >= :last_10_days"
        params["last_10_days"] = ten_days_ago
    
    sql += " ORDER BY t.txn_date DESC"
    
    result = db.session.execute(text(sql), params)
    sales = result.fetchall()
    
    # Calculate totals
    total_qty = sum(p.qty_liters for p in sales)
    total_amount = sum(p.amount for p in sales)
    avg_rate = (total_amount / total_qty) if total_qty > 0 else 0  # This is already per liter
    
    # Prepare data for template
    data = []
    for i, p in enumerate(sales, 1):
        # Calculate rate per liter for this transaction
        rate_per_liter = p.amount / p.qty_liters if p.qty_liters > 0 else 0
        
        # Get BF and SNF rates from chart if available, otherwise use the same calculation as milk entry
        bf_rate = 0
        snf_rate = 0
        if p.chart_id:
            chart = MilkRateChart.query.get(p.chart_id)
            if chart:
                bf_rate = chart.fat_rate
                snf_rate = chart.snf_rate
        else:
            # Use the same calculation as compute_component_breakdown function
            if p.rate > 0 and p.fat > 0 and p.snf > 0:
                # Use the exact same formula as compute_component_breakdown
                daily_rate = float(p.rate)
                fat_share = 0.60
                snf_share = 0.40
                std_fat_kg = 6.5
                std_snf_kg = 8.5
                
                # Calculate component rates (same as system formula)
                bf_rate_raw = (daily_rate * fat_share) / std_fat_kg
                snf_rate_raw = (daily_rate * snf_share) / std_snf_kg
                
                bf_rate = round(bf_rate_raw, 2)
                snf_rate = round(snf_rate_raw, 2)
            else:
                # Default standard rates
                bf_rate = 200  # Default fat rate
                snf_rate = 100  # Default SNF rate
        
        # Calculate BF kg and SNF kg
        bf_kg = p.qty_liters * p.fat / 100
        snf_kg = p.qty_liters * p.snf / 100
        
        # Extract buyer name from narration
        buyer_name = "Unknown"
        if p.narration and "Party:" in p.narration:
            # Extract party name from "Mobile Sale | Party: Party Name | ..."
            parts = p.narration.split("|")
            for part in parts:
                if "Party:" in part:
                    buyer_name = part.split("Party:")[1].strip()
                    break
        elif p.narration:
            # Fallback: if no Party: tag, try to extract from the first part
            first_part = p.narration.split("|")[0].strip()
            # If it's "Mobile Sale", we don't have a party name, keep "Unknown"
            if not first_part.startswith("Mobile"):
                buyer_name = first_part
        
        # Handle txn_date which might be string or date object
        if isinstance(p.txn_date, str):
            txn_date_str = p.txn_date
        else:
            txn_date_str = p.txn_date.strftime('%d-%m-%Y')
        
        data.append({
            'sr_no': i,
            'date': txn_date_str,
            'buyer': buyer_name,
            'description': f"Qty:{p.qty_liters}L | FAT:{p.fat}% | SNF:{p.snf}% | CLR:{p.clr} | BF:{bf_kg:.2f}kg | SNF:{snf_kg:.2f}kg | BF Rate:{bf_rate} | SNF Rate:{snf_rate} | Rate:{int(p.rate) if p.rate == int(p.rate) else p.rate}",
            'qty': p.qty_liters,
            'rate': rate_per_liter,  # Use calculated rate per liter
            'amount': p.amount
        })
    
    return render_template("milk/milk_sale_import.html", 
                         data=data, 
                         total_qty=total_qty,
                         total_amount=total_amount,
                         avg_rate=avg_rate,
                         party_search=party_search,
                         from_date=from_date,
                         to_date=to_date)

@milk_bp.route("/mobile-entry")
@login_required
def mobile_entry():
    """Mobile-optimized quick entry page"""
    return render_template("milk/mobile_entry.html")

@milk_bp.route("/mobile-save-entry", methods=["POST"])
@login_required
def mobile_save_entry():
    """Save milk entry from mobile interface with ALL features from main system"""
    try:
        cid = session.get("company_id")
        fy = session.get("fin_year")
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['date', 'party', 'qty', 'fat', 'clr', 'rate', 'type']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"success": False, "message": f"Missing required field: {field}"})
        
        # Parse and validate data
        from datetime import datetime
        txn_date = datetime.strptime(data['date'], "%Y-%m-%d").date()
        qty = float(data['qty'])
        fat = float(data['fat'])
        clr = float(data['clr'])
        rate = float(data['rate'])
        party_name = data['party'].strip()
        txn_type = data['type']
        
        # Validate transaction date is within financial year
        fy_start = date(int(fy[:4]), 4, 1)
        fy_end = date(int(fy[:4]) + 1, 3, 31)
        if not (fy_start <= txn_date <= fy_end):
            return jsonify({"success": False, "message": f"Date {txn_date} is outside financial year {fy}"})
        
        # Handle CLR conversion (if > 100, divide by 10)
        if clr > 100:
            clr = clr / 10.0
        
        # Handle FAT conversion (if > 10, divide by 10)
        if fat > 10:
            fat = fat / 10.0
        
        # Calculate SNF using Richmond's formula (SAME AS MAIN SYSTEM)
        snf = compute_snf(clr, fat)
        
        # Calculate amount using system formula
        calc = compute_component_breakdown(qty, fat, snf, rate)
        amount = calc["amount"]
        
        # Handle cash account or party account logic (SAME AS MAIN SYSTEM)
        is_cash_account = data.get('is_cash_account', False)
        
        if is_cash_account:
            # Use cash account
            party_id = None
            party_name = "Cash Account"
            
            # Get or create cash account
            cash_account = Account.query.filter_by(company_id=cid, name="Cash Account", account_type="Cash").first()
            if not cash_account:
                cash_account = Account(
                    company_id=cid,
                    name="Cash Account",
                    account_type="Cash",
                    group_name="Cash-in-Hand",
                    opening_dr=0.0,
                    opening_cr=0.0,
                    is_active=True
                )
                db.session.add(cash_account)
                db.session.flush()
            account_id = cash_account.id
            account = cash_account
        else:
            # Find or create party account (SAME AS MAIN SYSTEM)
            account = Account.query.filter_by(
                company_id=cid, 
                name=party_name,
                is_active=True
            ).first()
            
            if not account:
                # Create new account with proper group assignment
                account = Account(
                    company_id=cid,
                    name=party_name,
                    group_name="Sundry Creditors" if txn_type == "Purchase" else "Sundry Debtors",
                    opening_dr=0.0 if txn_type == "Purchase" else 0.0,
                    opening_cr=0.0 if txn_type == "Purchase" else 0.0,
                    is_active=True
                )
                db.session.add(account)
                db.session.flush()
            account_id = account.id
        
        # Create milk transaction using raw SQL to avoid account_id column issues
        from sqlalchemy import text
        
        # Check if we're using SQLite or PostgreSQL
        is_sqlite = db.engine.dialect.name == 'sqlite'
        
        if is_sqlite:
            # SQLite version without RETURNING
            milk_txn_sql = """
            INSERT INTO milk_transactions (
                company_id, fin_year, txn_date, shift, txn_type, 
                qty_liters, fat, snf, clr, rate, amount, chart_id, narration
            ) VALUES (
                :company_id, :fin_year, :txn_date, :shift, :txn_type,
                :qty_liters, :fat, :snf, :clr, :rate, :amount, :chart_id, :narration
            )
            """
            
            db.session.execute(text(milk_txn_sql), {
                "company_id": cid,
                "fin_year": fy,
                "txn_date": txn_date,
                "shift": "Mobile",
                "txn_type": txn_type,
                "qty_liters": qty,
                "fat": fat,
                "snf": snf,
                "clr": clr,
                "rate": rate,
                "amount": amount,
                "chart_id": None,
                "narration": f"Mobile {txn_type} | Party: {party_name} | FAT:{fat}% SNF:{snf}% | {qty}L @ Rs{rate}/100kg"
            })
            
            # Get the last inserted ID for SQLite
            milk_txn_id = db.session.execute(text("SELECT last_insert_rowid()")).scalar()
        else:
            # PostgreSQL version with RETURNING
            milk_txn_sql = """
            INSERT INTO milk_transactions (
                company_id, fin_year, txn_date, shift, txn_type, 
                qty_liters, fat, snf, clr, rate, amount, chart_id, narration
            ) VALUES (
                :company_id, :fin_year, :txn_date, :shift, :txn_type,
                :qty_liters, :fat, :snf, :clr, :rate, :amount, :chart_id, :narration
            ) RETURNING id
            """
            
            milk_result = db.session.execute(text(milk_txn_sql), {
                "company_id": cid,
                "fin_year": fy,
                "txn_date": txn_date,
                "shift": "Mobile",
                "txn_type": txn_type,
                "qty_liters": qty,
                "fat": fat,
                "snf": snf,
                "clr": clr,
                "rate": rate,
                "amount": amount,
                "chart_id": None,
                "narration": f"Mobile {txn_type} | Party: {party_name} | FAT:{fat}% SNF:{snf}% | {qty}L @ Rs{rate}/100kg"
            })
            
            milk_txn_id = milk_result.scalar()
        db.session.flush()
        
        # Handle invoice creation (AUTO-CREATE BY DEFAULT like main system)
        create_invoice = data.get('create_invoice', True)  # Default to True
        bill_no = None
        
        if create_invoice:
            bill_type = "Sales" if txn_type == "Sale" else "Purchase"
            
            # Generate bill number in P/0001/25-26 format
            last_bill = Bill.query.filter_by(company_id=cid, bill_type=bill_type).order_by(Bill.id.desc()).first()
            next_num = (last_bill.id + 1) if last_bill else 1
            prefix = "P" if bill_type == "Purchase" else "S"
            bill_no = f"{prefix}/{str(next_num).zfill(4)}/{fy}"
            
            # Handle GST (mobile defaults to 0% for simplicity)
            gst_rate = float(data.get('gst_rate', 0))
            gst_amt = round(amount * gst_rate / 100, 2)
            total = round(amount + gst_amt, 2)
            
            # Create bill
            bill = Bill(
                company_id=cid,
                fin_year=fy,
                party_id=None,  # Mobile entries don't link to party_id
                bill_no=bill_no,
                bill_date=txn_date,
                bill_type=bill_type,
                taxable_amount=amount,
                cgst=gst_amt/2,
                sgst=gst_amt/2,
                igst=0,
                total_amount=total,
                narration=f"Milk {txn_type} | FAT:{fat}% SNF:{snf}% | {qty}L @ Rs{rate}/100kg {'(Cash)' if is_cash_account else ''}",
                is_cancelled=False
            )
            db.session.add(bill)
            db.session.flush()
            
            # Create bill item
            item = BillItem(
                bill_id=bill.id,
                qty=qty,
                rate=rate,
                taxable_amount=amount,
                gst_rate=gst_rate,
                cgst=gst_amt/2,
                sgst=gst_amt/2,
                igst=0
            )
            db.session.add(item)
            
            # Link milk transaction to bill using raw SQL
            try:
                db.session.execute(text("""
                    UPDATE milk_transactions 
                    SET bill_id = :bill_id 
                    WHERE id = :milk_txn_id
                """), {"bill_id": bill.id, "milk_txn_id": milk_txn_id})
            except Exception as e:
                print(f"WARNING: Could not set bill_id (column may not exist): {e}")
        
        # Create journal entry (SAME AS MAIN SYSTEM)
        voucher_no = f"MLK-{milk_txn_id}"
        
        if txn_type == "Purchase":
            # Purchase: Debit Milk Purchase, Credit Supplier
            milk_purchase_acct = Account.query.filter_by(company_id=cid, name="Milk Purchase").first()
            if not milk_purchase_acct:
                milk_purchase_acct = Account(
                    company_id=cid, 
                    name="Milk Purchase", 
                    group_name="Direct Expenses", 
                    opening_dr=0.0, 
                    opening_cr=0.0, 
                    is_active=True
                )
                db.session.add(milk_purchase_acct)
                db.session.flush()
            
            header = JournalHeader(
                company_id=cid,
                fin_year=fy,
                voucher_type="Journal",
                voucher_no=voucher_no,
                voucher_date=txn_date,
                narration=f"Mobile Milk Purchase | FAT:{fat}% SNF:{snf}% | {qty}L @ Rs{rate}/100kg | {voucher_no}"
            )
            db.session.add(header)
            db.session.flush()
            
            # Debit Milk Purchase
            db.session.add(JournalLine(
                journal_header_id=header.id,
                account_id=milk_purchase_acct.id,
                debit=amount,
                credit=0,
                narration=header.narration
            ))
            
            # Credit Supplier
            db.session.add(JournalLine(
                journal_header_id=header.id,
                account_id=account.id,
                debit=0,
                credit=amount,
                narration=header.narration
            ))
            
        else:  # Sale
            # Sale: Debit Customer, Credit Milk Sale
            milk_sale_acct = Account.query.filter_by(company_id=cid, name="Milk Sale").first()
            if not milk_sale_acct:
                milk_sale_acct = Account(
                    company_id=cid, 
                    name="Milk Sale", 
                    group_name="Direct Incomes", 
                    opening_dr=0.0, 
                    opening_cr=0.0, 
                    is_active=True
                )
                db.session.add(milk_sale_acct)
                db.session.flush()
            
            header = JournalHeader(
                company_id=cid,
                fin_year=fy,
                voucher_type="Journal",
                voucher_no=voucher_no,
                voucher_date=txn_date,
                narration=f"Mobile Milk Sale | FAT:{fat}% SNF:{snf}% | {qty}L @ Rs{rate}/100kg | {voucher_no}"
            )
            db.session.add(header)
            db.session.flush()
            
            # Debit Customer
            db.session.add(JournalLine(
                journal_header_id=header.id,
                account_id=account.id,
                debit=amount,
                credit=0,
                narration=header.narration
            ))
            
            # Credit Milk Sale
            db.session.add(JournalLine(
                journal_header_id=header.id,
                account_id=milk_sale_acct.id,
                debit=0,
                credit=amount,
                narration=header.narration
            ))
        
        # Update session with last entry date and account (SAME AS MAIN SYSTEM)
        session["last_txn_date"] = txn_date.isoformat()
        if not is_cash_account:
            session["last_milk_account_id"] = account_id
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Entry saved successfully" + (f" | Invoice {bill_no} created" if create_invoice else ""),
            "entry_id": milk_txn_id,
            "amount": amount,
            "bill_no": bill_no,
            "voucher_no": voucher_no
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving mobile entry: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error saving entry: {str(e)}"
        })

@milk_bp.route("/get-last-entry")
@login_required
def get_last_entry():
    """Get the last milk entry for mobile display"""
    try:
        cid = session.get("company_id")
        fy = session.get("fin_year")
        
        from models import MilkTransaction, Account
        from sqlalchemy import text
        
        # Get last entry
        sql = """
        SELECT t.id, t.txn_date, t.qty_liters, t.fat, t.clr, t.rate, t.amount, t.txn_type,
               CASE 
                 WHEN t.narration LIKE '%Party:%' THEN 
                   SUBSTR(t.narration, 
                          INSTR(t.narration, 'Party:') + 6, 
                          CASE 
                            WHEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') > 0 
                            THEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') - 1
                            ELSE LENGTH(t.narration) - INSTR(t.narration, 'Party:') - 5
                          END
                   )
                 ELSE 'Unknown'
               END as party_name
        FROM milk_transactions t
        WHERE t.company_id = :company_id AND t.fin_year = :fin_year
        ORDER BY t.txn_date DESC, t.id DESC
        LIMIT 1
        """
        
        result = db.session.execute(text(sql), {
            "company_id": cid,
            "fin_year": fy
        })
        row = result.fetchone()
        
        if row:
            return jsonify({
                "success": True,
                "entry": {
                    "date": row.txn_date.isoformat() if row.txn_date else None,
                    "party": row.party_name or "",
                    "qty": float(row.qty_liters),
                    "fat": float(row.fat),
                    "clr": float(row.clr),
                    "rate": float(row.rate),
                    "amount": float(row.amount),
                    "type": row.txn_type
                }
            })
        else:
            return jsonify({"success": False, "message": "No entries found"})
            
    except Exception as e:
        print(f"Error getting last entry: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@milk_bp.route("/get-today-stats")
@login_required
def get_today_stats():
    """Get today's entry statistics for mobile display"""
    try:
        cid = session.get("company_id")
        fy = session.get("fin_year")
        
        from models import MilkTransaction
        from sqlalchemy import text
        
        today = date.today()
        
        sql = """
        SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
        FROM milk_transactions
        WHERE company_id = :company_id AND fin_year = :fin_year 
              AND DATE(txn_date) = :today
        """
        
        result = db.session.execute(text(sql), {
            "company_id": cid,
            "fin_year": fy,
            "today": today
        })
        row = result.fetchone()
        
        return jsonify({
            "success": True,
            "count": row.count if row else 0,
            "total": float(row.total) if row and row.total else 0.0
        })
        
    except Exception as e:
        print(f"Error getting today stats: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@milk_bp.route("/entry/add", methods=["GET","POST"])
def add_entry():
    # Initialize session if not set
    if not session.get("company_id"):
        session["company_id"] = 1
        session["company_name"] = "Default Company"
        session["fin_year"] = "2025-26"
        session["user_role"] = "admin"
    
    cid = session.get("company_id"); fy = session.get("fin_year")
    accounts = Account.query.filter_by(company_id=cid, is_active=True).order_by(Account.name).all()
    
    # Add default account if none exist
    if not accounts:
        default_account = Account(
            company_id=cid,
            name="Shivam Grover",
            group_name="Sundry Debtors",
            opening_dr=0.0,
            is_active=True
        )
        db.session.add(default_account)
        db.session.commit()
        accounts = [default_account]
    
    charts  = MilkRateChart.query.filter_by(company_id=cid, is_active=True).order_by(MilkRateChart.effective_date.desc()).all()
    default_date = session.get("last_txn_date") or date.today().isoformat()
    last_account_id = session.get("last_milk_account_id")
    last_account = Account.query.filter_by(id=last_account_id, company_id=cid).first() if last_account_id else None
    
    # Get last milk entry for display
    last_entry = None
    try:
        from sqlalchemy import text
        sql = """
        SELECT t.id, t.company_id, t.fin_year, t.voucher_no, t.txn_date, t.shift, 
               t.txn_type, t.qty_liters, t.fat, t.snf, t.clr, t.rate, t.amount, t.chart_id, t.narration,
               'Unknown' as account_name
        FROM milk_transactions t
        WHERE t.company_id = :company_id 
        ORDER BY t.txn_date DESC, t.id DESC
        LIMIT 1
        """
        result = db.session.execute(text(sql), {"company_id": cid})
        row = result.fetchone()
        if row:
            class LastMilkEntry:
                def __init__(self, row):
                    self.id = row.id
                    # Handle date conversion properly
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
                    self.clr = row.clr
                    self.rate = row.rate
                    self.amount = row.amount
                    self.account_name = row.account_name or "Cash Account"
                    self.narration = row.narration
            last_entry = LastMilkEntry(row)
    except Exception as e:
        print(f"DEBUG: Could not fetch last entry: {e}")
        last_entry = None
    
    if request.method == "POST":
        # Validate that transaction date is within the selected financial year
        from datetime import datetime
        try:
            txn_date = datetime.strptime(request.form["txn_date"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            flash("Invalid transaction date", "danger")
            return redirect(url_for("milk.add_entry"))
        
        # Check if transaction date is within the selected FY
        fy_start = date(int(fy[:4]), 4, 1)
        fy_end = date(int(fy[:4]) + 1, 3, 31)
        if not (fy_start <= txn_date <= fy_end):
            flash(f"Transaction date {txn_date} is outside the selected financial year {fy}. Allowed dates: {fy_start} to {fy_end}", "danger")
            return redirect(url_for("milk.add_entry"))
        
        fat=float(request.form["fat"]) 
        if fat > 10:
            fat = fat / 10.0
        qty=float(request.form["qty_liters"])
        
        # Handle CLR conversion
        clr=float(request.form.get("clr", 0))
        # If CLR > 100, divide by 10 (289 -> 28.9)
        if clr > 100:
            clr = clr / 10.0
        
        # Handle rate chart selection
        chart_id=to_int_or_none(request.form.get("chart_id"))
        if chart_id:
            chart=MilkRateChart.query.get(int(chart_id))
            fat_rate=chart.fat_rate; snf_rate=chart.snf_rate
        else:
            fat_rate=float(request.form.get("fat_rate", 200))
            snf_rate=float(request.form.get("snf_rate", 100))
        
        # Calculate SNF using Richmond's formula
        if clr > 0 and fat > 0:
            snf = compute_snf(clr, fat)
        else:
            snf = float(request.form.get("snf_auto", 8.5))

        # Always prefer user-entered Daily Rate (per 100kg) for storage & calculation
        daily_rate = float((request.form.get("rate_per_liter") or 0) or 0)
        if daily_rate > 0:
            calc = compute_component_breakdown(qty, fat, snf, daily_rate)
            amount = calc["amount"]
            rate = daily_rate
        else:
            amount_str = (request.form.get("amount") or "").strip()
            calc_rate_str = (request.form.get("calc_rate") or "").strip()
            if amount_str:
                amount = float(amount_str)
                if calc_rate_str:
                    rate = float(calc_rate_str)
                else:
                    rate = round((amount / qty) * 100, 2) if qty else 0
            else:
                rate = calc_rate(fat, snf, fat_rate, snf_rate)
                amount = round(rate * qty, 2)
        
        txn_type=request.form["txn_type"]; 
        # txn_date already parsed and validated above
        create_invoice=request.form.get("create_invoice")=="1"
        print(f"DEBUG: create_invoice = {create_invoice}")
        print(f"DEBUG: form data = {dict(request.form)}")
        
        # Handle cash account or party account logic
        is_cash_account = request.form.get('is_cash_account') == 'on'
        
        if is_cash_account:
            # Use cash account
            party_id = None
            party_name = "Cash Account"
            print(f"DEBUG: Using cash account mode")
            
            # Get or create cash account
            cash_account = Account.query.filter_by(company_id=cid, name="Cash Account", account_type="Cash").first()
            if not cash_account:
                cash_account = Account(
                    company_id=cid,
                    name="Cash Account",
                    account_type="Cash",
                    group_name="Cash-in-Hand",
                    opening_dr=0.0,
                    opening_cr=0.0,
                    is_active=True
                )
                db.session.add(cash_account)
                db.session.flush()
                print(f"DEBUG: Created cash account: {cash_account.name}")
            account_id = cash_account.id
        else:
            # Use account
            account_id_str = request.form.get("party_id", "").strip()
            if not account_id_str or account_id_str == 'cash':
                flash("Please select an account", "error")
                return redirect(url_for('milk.add_entry'))
            account_id=int(account_id_str)
            account = Account.query.get(account_id)
            if not account:
                flash("Invalid account selected", "error")
                return render_template("milk/entry_form_traditional.html", accounts=accounts, charts=charts, today=default_date, edit_mode=False, default_account=last_account)
        
        # Create milk transaction using raw SQL to avoid account_id column issues
        from sqlalchemy import text
        
        # Check if we're using SQLite or PostgreSQL
        is_sqlite = db.engine.dialect.name == 'sqlite'
        
        # Build narration with party info
        party_name = "Cash Account"
        if not is_cash_account and account:
            party_name = account.name
        
        narration = f"Mobile Purchase | Party: {party_name} | FAT:{fat}% SNF:{snf}% | {qty}L @ Rs{rate}/100kg"
        if request.form.get("narration", "").strip():
            narration = request.form.get("narration", "").strip()
        
        # Insert milk transaction
        if is_sqlite:
            # SQLite version
            sql = """
            INSERT INTO milk_transactions 
            (company_id, fin_year, voucher_no, txn_date, shift, txn_type, 
             qty_liters, fat, snf, clr, rate, amount, chart_id, narration)
            VALUES 
            (:company_id, :fin_year, :voucher_no, :txn_date, :shift, :txn_type,
             :qty_liters, :fat, :snf, :clr, :rate, :amount, :chart_id, :narration)
            """
            result = db.session.execute(text(sql), {
                "company_id": cid,
                "fin_year": fy,
                "voucher_no": f"MKT{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "txn_date": txn_date,
                "shift": request.form.get("shift", "Morning"),
                "txn_type": txn_type,
                "qty_liters": qty,
                "fat": fat,
                "snf": snf,
                "clr": clr,
                "rate": rate,
                "amount": amount,
                "chart_id": chart_id,
                "narration": narration
            })
            txn_id = result.lastrowid
        else:
            # PostgreSQL version
            sql = """
            INSERT INTO milk_transactions 
            (company_id, fin_year, voucher_no, txn_date, shift, txn_type, 
             qty_liters, fat, snf, clr, rate, amount, chart_id, narration)
            VALUES 
            (:company_id, :fin_year, :voucher_no, :txn_date, :shift, :txn_type,
             :qty_liters, :fat, :snf, :clr, :rate, :amount, :chart_id, :narration)
            RETURNING id
            """
            result = db.session.execute(text(sql), {
                "company_id": cid,
                "fin_year": fy,
                "voucher_no": f"MKT{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "txn_date": txn_date,
                "shift": request.form.get("shift", "Morning"),
                "txn_type": txn_type,
                "qty_liters": qty,
                "fat": fat,
                "snf": snf,
                "clr": clr,
                "rate": rate,
                "amount": amount,
                "chart_id": chart_id,
                "narration": narration
            })
            row = result.fetchone()
            txn_id = row.id
        
        print(f"DEBUG: Created milk transaction with ID: {txn_id}")
        
        bill_no=None
        if create_invoice:
            print(f"DEBUG: Creating invoice for transaction {txn_id}")
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

            party_id = None
            
            bill=Bill(company_id=cid,fin_year=fy,party_id=party_id,bill_no=bill_no,
                bill_date=txn_date,bill_type=bill_type,taxable_amount=amount,
                cgst=gst_amt/2, sgst=gst_amt/2, igst=0, total_amount=total,
                narration=f"Milk {txn_type} | FAT:{fat}% SNF:{snf}% | {qty}L @ Rs{rate}/100kg {'(Cash)' if is_cash_account else ''}",
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
            print(f"DEBUG: Setting milk transaction bill_id = {bill.id}")
            
            # Update milk transaction with bill_id
            if is_sqlite:
                db.session.execute(text("UPDATE milk_transactions SET bill_id = :bill_id WHERE id = :txn_id"), 
                                 {"bill_id": bill.id, "txn_id": txn_id})
            else:
                db.session.execute(text("UPDATE milk_transactions SET bill_id = :bill_id WHERE id = :txn_id"), 
                                 {"bill_id": bill.id, "txn_id": txn_id})
            
            print(f"DEBUG: Invoice creation completed")
            
            # Post to ledgers with correct debit/credit based on transaction type
            try:
                if txn_type == 'Purchase':
                    # Purchase: Debit Milk Purchase (expense), Credit Supplier (you owe them)
                    milk_purchase_acct = Account.query.filter_by(company_id=cid, name="Milk Purchase").first()
                    if not milk_purchase_acct:
                        milk_purchase_acct = Account(company_id=cid, name="Milk Purchase", group_name="Direct Expenses", opening_dr=0.0, opening_cr=0.0, is_active=True)
                        db.session.add(milk_purchase_acct)
                        db.session.flush()
                    
                    selected_acct = Account.query.get(account_id) if account_id else None
                    if selected_acct:
                        voucher_no = f"MLK-{txn_id}"
                        header = JournalHeader(
                            company_id=cid,
                            fin_year=fy,
                            voucher_type="Journal",
                            voucher_no=voucher_no,
                            voucher_date=txn_date,
                            narration=f"Milk {txn_type} | FAT:{fat}% SNF:{snf}% | {qty}L @ Rs{rate}/100kg | {voucher_no}"
                        )
                        db.session.add(header)
                        db.session.flush()
                        # Debit Milk Purchase (expense increases)
                        db.session.add(JournalLine(
                            journal_header_id=header.id,
                            account_id=milk_purchase_acct.id,
                            debit=amount,
                            credit=0,
                            narration=header.narration
                        ))
                        # Credit Supplier (you owe them, liability increases)
                        db.session.add(JournalLine(
                            journal_header_id=header.id,
                            account_id=selected_acct.id,
                            debit=0,
                            credit=amount,
                            narration=header.narration
                        ))
                        print(f"DEBUG: Purchase entry posted - Debit Milk Purchase: {amount}, Credit Supplier: {amount}")
                        
                elif txn_type == 'Sale':
                    # Sale: Debit Supplier (they owe you), Credit Milk Sale (income)
                    milk_sale_acct = Account.query.filter_by(company_id=cid, name="Milk Sale").first()
                    if not milk_sale_acct:
                        milk_sale_acct = Account(company_id=cid, name="Milk Sale", group_name="Direct Incomes", opening_dr=0.0, opening_cr=0.0, is_active=True)
                        db.session.add(milk_sale_acct)
                        db.session.flush()
                    
                    selected_acct = Account.query.get(account_id) if account_id else None
                    if selected_acct:
                        voucher_no = f"MLK-{txn_id}"
                        header = JournalHeader(
                            company_id=cid,
                            fin_year=fy,
                            voucher_type="Journal",
                            voucher_no=voucher_no,
                            voucher_date=txn_date,
                            narration=f"Milk {txn_type} | FAT:{fat}% SNF:{snf}% | {qty}L @ Rs{rate}/100kg | {voucher_no}"
                        )
                        db.session.add(header)
                        db.session.flush()
                        # Debit Supplier (they owe you, asset increases)
                        db.session.add(JournalLine(
                            journal_header_id=header.id,
                            account_id=selected_acct.id,
                            debit=amount,
                            credit=0,
                            narration=header.narration
                        ))
                        # Credit Milk Sale (income increases)
                        db.session.add(JournalLine(
                            journal_header_id=header.id,
                            account_id=milk_sale_acct.id,
                            debit=0,
                            credit=amount,
                            narration=header.narration
                        ))
                        print(f"DEBUG: Sale entry posted - Debit Supplier: {amount}, Credit Milk Sale: {amount}")
                
                db.session.commit()
                print(f"DEBUG: Journal posting committed successfully")
            except Exception as e:
                print(f"DEBUG: Ledger posting failed: {e}")
                db.session.rollback()
            
            # Party ledger works via Bills + CashBook + JournalLines
            # No separate Account record needed - prevents duplicate entries
            
            db.session.commit()
            session["last_txn_date"] = txn_date.isoformat()
            if account_id:
                session["last_milk_account_id"] = account_id
            msg=f"Saved {qty}L @ Rs{rate}/100kg = Rs{amount}"
            if bill_no: msg+=f" | Invoice {bill_no} created"
            flash(msg,"success")
            return redirect(url_for("milk.add_entry"))  # Redirect back to add entry page

        db.session.commit()
        session["last_txn_date"] = txn_date.isoformat()
        if account_id:
            session["last_milk_account_id"] = account_id
        
        # Post to ledgers: debit Milk Purchase, credit selected account
        try:
            print(f"DEBUG: Starting journal posting for account_id={account_id}")
            milk_purchase_acct = Account.query.filter_by(company_id=cid, name="Milk Purchase").first()
            if not milk_purchase_acct:
                milk_purchase_acct = Account(company_id=cid, name="Milk Purchase", group_name="Direct Expenses", opening_dr=0.0, opening_cr=0.0, is_active=True)
                db.session.add(milk_purchase_acct)
                db.session.flush()
                print(f"DEBUG: Created Milk Purchase account id={milk_purchase_acct.id}")
            selected_acct = Account.query.get(account_id) if account_id else None
            if selected_acct:
                voucher_no = f"MLK-{txn_id}"
                header = JournalHeader(
                    company_id=cid,
                    fin_year=session.get("fin_year"),  # Use session FY (validated to match txn date)
                    voucher_type="Journal",
                    voucher_no=voucher_no,
                    voucher_date=txn_date,
                    narration=f"Milk {txn_type} | FAT:{fat}% SNF:{snf}% | {qty}L @ Rs{rate}/100kg | {voucher_no}"
                )
                db.session.add(header)
                db.session.flush()
                print(f"DEBUG: Created JournalHeader id={header.id}")
                # Debit Milk Purchase
                db.session.add(JournalLine(
                    journal_header_id=header.id,
                    account_id=milk_purchase_acct.id,
                    debit=amount,
                    credit=0,
                    narration=header.narration
                ))
                # Credit selected account
                db.session.add(JournalLine(
                    journal_header_id=header.id,
                    account_id=selected_acct.id,
                    debit=0,
                    credit=amount,
                    narration=header.narration
                ))
                print(f"DEBUG: Created JournalLines for debit={amount} and credit={amount}")
                db.session.commit()
                print(f"DEBUG: Journal posting committed successfully")
            else:
                print(f"DEBUG: No selected account found for account_id={account_id}")
        except Exception as e:
            print(f"DEBUG: Ledger posting failed: {e}")
            db.session.rollback()
        
        msg=f"Saved {qty}L @ Rs{rate}/100kg = Rs{amount}"
        flash(msg,"success")
        return redirect(url_for("milk.add_entry"))  # Redirect back to add entry page
        
    return render_template("milk/entry_form_traditional.html", accounts=accounts, charts=charts, today=default_date, edit_mode=False, default_account=last_account, last_entry=last_entry)

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
    
    accounts = Account.query.filter_by(company_id=cid, is_active=True).order_by(Account.name).all()
    
    # Add default account if none exist
    if not accounts:
        default_account = Account(
            company_id=cid,
            name="Shivam Grover",
            group_name="Sundry Debtors",
            opening_dr=0.0,
            is_active=True
        )
        db.session.add(default_account)
        db.session.commit()
        accounts = [default_account]
    
    charts  = MilkRateChart.query.filter_by(company_id=cid, is_active=True).order_by(MilkRateChart.effective_date.desc()).all()
    
    # Get existing transaction - use raw SQL to avoid ORM issues
    from sqlalchemy import text
    sql = """
    SELECT id, company_id, fin_year, voucher_no, txn_date, shift, 
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
        
        # Get account information for this transaction
        account_name = "Cash Account"
        # Extract party name from narration if available
        if row.narration and "Party:" in row.narration:
            # Extract party name from "Mobile Purchase | Party: Party Name | ..."
            parts = row.narration.split("|")
            for part in parts:
                if "Party:" in part:
                    account_name = part.split("Party:")[1].strip()
                    break
        print(f"  Account: {account_name}")

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
                self.account_id = None  # No account_id in new schema
                # Add account object for template compatibility
                class SimpleAccount:
                    def __init__(self, name, id):
                        self.name = name
                        self.id = id
                self.account = SimpleAccount(account_name, None)
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
        
        # Handle party_id safely - can be None for mobile entries
        party_id_raw = request.form.get("party_id")
        actual_txn.party_id = (
            int(party_id_raw)
            if party_id_raw
            and str(party_id_raw).strip()
            and str(party_id_raw).strip().lower() != 'none'
            else None
        )
        
        actual_txn.qty_liters = float(request.form["qty_liters"])
        qty = actual_txn.qty_liters

        fat_val = float(request.form["fat"])
        if fat_val > 10:
            fat_val = fat_val / 10.0
        actual_txn.fat = fat_val

        clr_val = float(request.form.get("clr", 0.0))  # CLR might not exist in DB
        if clr_val > 100:
            clr_val = clr_val / 10.0
        actual_txn.clr = clr_val

        # Always re-calc SNF from CLR/FAT
        if actual_txn.clr > 0 and actual_txn.fat > 0:
            calculated_snf = compute_snf(actual_txn.clr, actual_txn.fat)
            actual_txn.snf = calculated_snf
        else:
            actual_txn.snf = float(request.form.get("snf_auto", 8.5))

        # Traditional Indian Milk Pricing Method (SNF Method)
        daily_rate_str = (request.form.get("rate_per_liter") or "").strip()
        amount_str = (request.form.get("amount") or "").strip()
        
        if daily_rate_str and daily_rate_str != '0':
            daily_rate = float(daily_rate_str)
            print(f"DEBUG: Using traditional method with daily rate: {daily_rate}")
            calc = compute_component_breakdown(qty, actual_txn.fat, actual_txn.snf, daily_rate)
            bf_kgs = calc["bf_kgs"]
            snf_kgs = calc["snf_kgs"]
            ghee_rate = calc["bf_rate"]
            powder_rate = calc["snf_rate"]
            
            print(f"DEBUG: Using calculated SNF: {actual_txn.snf:.2f} (stored SNF: {actual_txn.snf:.2f})")
            
            ghee_amount = _round2(bf_kgs * ghee_rate)
            powder_amount = _round2(snf_kgs * powder_rate)
            final_amount = calc["amount"]

            # Store the daily rate as rate per 100kg (not calculated from amount)
            actual_txn.rate = daily_rate  # Store as rate per 100kg
            actual_txn.amount = final_amount
            
            print(f"DEBUG: Traditional calculation:")
            print(f"  Ghee: {bf_kgs:.3f}kg × ₹{ghee_rate:.2f} = ₹{ghee_amount:.2f}")
            print(f"  Powder: {snf_kgs:.3f}kg × ₹{powder_rate:.2f} = ₹{powder_amount:.2f}")
            print(f"  Total: ₹{final_amount:.2f}")
            
        elif amount_str:
            actual_txn.amount = float(amount_str)
            # Calculate rate per 100kg from amount
            actual_txn.rate = round((actual_txn.amount / qty) * 100, 2) if qty else 0
            print(f"DEBUG: Using provided amount: {actual_txn.amount}, calculated rate: {actual_txn.rate}")
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
        session["last_txn_date"] = actual_txn.txn_date.isoformat()
        print(f"DEBUG: After update - FAT: {actual_txn.fat}, SNF: {actual_txn.snf}, RATE: {actual_txn.rate}, AMOUNT: {actual_txn.amount}")
        print("DEBUG: Database commit successful!")
        flash(f"Milk entry updated successfully", "success")
        return redirect(url_for("milk.entry_list"))
    
    # Pre-fill form with existing data
    return render_template("milk/entry_form_traditional.html", 
                     accounts=accounts, charts=charts, 
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
            # Convert fat input (user enters 44 → 4.4)
            fat_value = float(value)
            if fat_value > 10:
                fat_value = fat_value / 10.0
            txn.fat = fat_value
        elif field == "snf":
            txn.snf = float(value)
        elif field == "rate":
            # Rate should be stored as per 100kg
            rate_value = float(value)
            # If user entered rate per litre (small number), convert to per 100kg
            if rate_value < 100:
                rate_value = rate_value * 100
            txn.rate = rate_value
        elif field == "clr":
            # Convert CLR input (user enters 295 → 29.5)
            clr_value = float(value)
            if clr_value > 100:
                clr_value = clr_value / 10.0
            txn.clr = clr_value
        
        # Recalculate SNF using Richmond's formula if CLR and FAT are available
        if hasattr(txn, 'clr') and hasattr(txn, 'fat') and txn.clr > 0 and txn.fat > 0:
            txn.snf = compute_snf(txn.clr, txn.fat)
        
        # Recalculate amount using component method if daily rate is available
        if hasattr(txn, 'rate') and txn.rate > 0 and txn.qty_liters > 0:
            calc = compute_component_breakdown(txn.qty_liters, txn.fat, txn.snf, txn.rate)
            txn.amount = calc["amount"]
        
        db.session.commit()
        return jsonify({"success": True, "message": "Updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})

@milk_bp.route("/admin/update-all-milk-calculations")
@login_required
def update_all_milk_calculations():
    """Update all existing milk transactions to use Milk Chief compatible formula"""
    try:
        cid = session.get("company_id"); fy = session.get("fin_year")
        
        # Get all milk transactions
        txns = MilkTransaction.query.filter_by(company_id=cid, fin_year=fy).all()
        
        updated_count = 0
        for txn in txns:
            # Normalize fat (handle old double-divided values like 0.43 instead of 4.3)
            if txn.fat and txn.fat > 10:
                txn.fat = txn.fat / 10.0
            elif txn.fat and 0 < txn.fat < 1:
                txn.fat = txn.fat * 10.0

            # Normalize CLR
            if hasattr(txn, 'clr') and txn.clr:
                if txn.clr > 100:
                    txn.clr = txn.clr / 10.0
                elif 0 < txn.clr < 10:
                    txn.clr = txn.clr * 10.0
            
            # Recalculate SNF using Richmond's formula
            if hasattr(txn, 'clr') and txn.clr > 0 and txn.fat > 0:
                txn.snf = compute_snf(txn.clr, txn.fat)

            # Fix stored daily rate (per 100kg)
            if txn.qty_liters and txn.qty_liters > 0:
                if txn.amount and txn.amount > 0 and txn.fat and txn.fat > 0 and txn.snf and txn.snf > 0:
                    bf_kgs = round(txn.qty_liters * txn.fat / 100.0, 3)
                    snf_kgs = round(txn.qty_liters * txn.snf / 100.0, 3)
                    denom = (bf_kgs * (0.60 / 6.5)) + (snf_kgs * (0.40 / 8.5))
                    if denom > 0:
                        txn.rate = round(float(txn.amount) / denom, 2)
                elif txn.rate and 0 < txn.rate < 100:
                    txn.rate = txn.rate * 100
            
            # Recalculate amount using component method if rate is available
            if txn.rate > 0 and txn.qty_liters > 0:
                calc = compute_component_breakdown(txn.qty_liters, txn.fat, txn.snf, txn.rate)
                txn.amount = calc["amount"]
            
            updated_count += 1
        
        db.session.commit()
        flash(f"Updated {updated_count} milk transactions with Milk Chief compatible calculations", "success")
        return jsonify({"success": True, "updated": updated_count})
        
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
    from models import Company, Account
    company = Company.query.get(cid)
    
    # Get related account (supplier/buyer) from milk transaction
    account = None
    if milk_transaction and milk_transaction.account_id:
        account = Account.query.get(milk_transaction.account_id)
    
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
                         account=account,
                         float=decimal_to_float)

@milk_bp.route("/milk/summary")
def summary():
    cid=session.get("company_id"); fy=session.get("fin_year")
    from sqlalchemy import func
    data=db.session.query(MilkTransaction.txn_type,Account.name,
        func.sum(MilkTransaction.qty_liters).label("total_qty"),
        func.sum(MilkTransaction.amount).label("total_amt"),
        func.avg(MilkTransaction.fat).label("avg_fat"),
        func.avg(MilkTransaction.snf).label("avg_snf"),
    ).join(Account,MilkTransaction.account_id==Account.id).filter(
        MilkTransaction.company_id==cid,MilkTransaction.fin_year==fy
    ).group_by(MilkTransaction.txn_type,Account.name).all()
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

@milk_bp.route("/parties/search", methods=["GET"])
def search_parties():
    """Search parties with ledger and balance information for autocomplete"""
    try:
        cid = session.get("company_id", 1)
        search_term = request.args.get("q", "").strip()
        
        # Get parties matching search term
        query = Party.query.filter_by(company_id=cid, is_active=True)
        
        if search_term:
            query = query.filter(Party.name.ilike(f"%{search_term}%"))
        
        parties = query.order_by(Party.name).limit(50).all()
        
        # Format results with balance information
        results = []
        for party in parties:
            # Calculate current balance (opening + transactions)
            opening_balance = float(party.opening_balance or 0)
            balance_type = party.balance_type or 'Dr'
            
            # Get transaction totals for this party
            from models import Bill
            bills = Bill.query.filter_by(
                party_id=party.id,
                company_id=cid,
                is_cancelled=False
            ).all()
            
            transaction_total = sum(float(bill.total_amount or 0) for bill in bills)
            
            # Calculate current balance
            if balance_type == 'Dr':
                current_balance = opening_balance + transaction_total
            else:
                current_balance = -opening_balance + transaction_total
            
            results.append({
                'id': party.id,
                'name': party.name,
                'phone': party.phone or '',
                'gstin': party.gstin or '',
                'opening_balance': opening_balance,
                'balance_type': balance_type,
                'current_balance': current_balance,
                'balance_display': f"₹{abs(current_balance):,.2f} {'Dr' if current_balance >= 0 else 'Cr'}"
            })
        
        return jsonify({
            'success': True,
            'parties': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'parties': []
        })

@milk_bp.route("/parties/add", methods=["POST"])
def add_party():
    """Add a new party via AJAX - consistent with clients module"""
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
        
        # Determine party type - default to "Both" for milk suppliers (can be both debtor and creditor)
        party_type = "Both"  # Milk parties can both supply milk (creditor) and purchase goods (debtor)
        
        party = Party(
            company_id=cid,
            name=name,
            phone=request.form.get("phone", "").strip() or None,
            email=request.form.get("email", "").strip() or None,
            gstin=request.form.get("gst_number", "").strip().upper() or None,
            address=request.form.get("address", "").strip() or None,
            state_code=request.form.get("state_code", "").strip() or None,
            party_type=party_type,
            balance_type="Dr",  # Default balance type
            opening_balance=0.0,  # Default opening balance
            is_active=True
        )
        
        db.session.add(party)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "id": party.id,
            "name": party.name,
            "party_type": party.party_type,
            "phone": party.phone or "",
            "gstin": party.gstin or "",
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
    
    try:
        # Use raw SQL to avoid account_id column issues
        from sqlalchemy import text
        
        # Get the milk transaction details first
        result = db.session.execute(text("""
            SELECT id, bill_id FROM milk_transactions 
            WHERE id = :txn_id AND company_id = :company_id AND fin_year = :fin_year
        """), {"txn_id": txn_id, "company_id": cid, "fin_year": fy})
        
        txn_row = result.fetchone()
        if not txn_row:
            flash("Milk entry not found", "error")
            return redirect(url_for('milk.entry_list'))
        
        print(f"DEBUG: Deleting milk transaction {txn_id}")
        
        # Delete associated bill if exists
        if txn_row.bill_id:
            print(f"DEBUG: Deleting associated bill {txn_row.bill_id}")
            # Delete bill items first
            db.session.execute(text("DELETE FROM bill_items WHERE bill_id = :bill_id"), {"bill_id": txn_row.bill_id})
            # Delete the bill
            db.session.execute(text("DELETE FROM bills WHERE id = :bill_id"), {"bill_id": txn_row.bill_id})
        
        # Delete any journal entries related to this milk transaction
        # Journal entries might reference this transaction in their narration
        print(f"DEBUG: Checking for related journal entries...")
        journal_result = db.session.execute(text("""
            SELECT jh.id FROM journal_headers jh 
            WHERE jh.narration LIKE :txn_pattern
        """), {"txn_pattern": f"%MLK-{txn_id}%"})
        
        journal_headers = journal_result.fetchall()
        for jh in journal_headers:
            print(f"DEBUG: Deleting journal header {jh.id} and its lines")
            # Delete journal lines first
            db.session.execute(text("DELETE FROM journal_lines WHERE journal_header_id = :jh_id"), {"jh_id": jh.id})
            # Delete journal header
            db.session.execute(text("DELETE FROM journal_headers WHERE id = :jh_id"), {"jh_id": jh.id})
        
        # Delete the milk transaction
        print(f"DEBUG: Deleting milk transaction {txn_id}")
        db.session.execute(text("DELETE FROM milk_transactions WHERE id = :txn_id"), {"txn_id": txn_id})
        db.session.commit()
        
        print(f"DEBUG: Milk transaction {txn_id} deleted successfully")
        flash("Milk entry deleted successfully", "success")
        return redirect(url_for('milk.entry_list'))
    
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Error deleting milk entry {txn_id}: {str(e)}")
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
    
    # Use raw SQL to avoid account_id column issues
    from sqlalchemy import text
    sql = """
    SELECT t.id, t.txn_date, t.qty_liters, t.fat, t.snf, t.clr, t.rate, t.amount, t.narration,
           CASE 
             WHEN t.narration LIKE '%Party:%' THEN 
               SUBSTR(t.narration, 
                      INSTR(t.narration, 'Party:') + 6, 
                      CASE 
                        WHEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') > 0 
                        THEN INSTR(SUBSTR(t.narration, INSTR(t.narration, 'Party:') + 6), '|') - 1
                        ELSE LENGTH(t.narration) - INSTR(t.narration, 'Party:') - 5
                      END
               )
             ELSE 'Unknown'
           END as party_name
    FROM milk_transactions t
    WHERE t.company_id = :company_id AND t.fin_year = :fin_year
    ORDER BY t.id
    """
    result = db.session.execute(text(sql), {"company_id": cid, "fin_year": fy})
    txns = result.fetchall()

    lines = []
    for t in txns:
        # Use party_name from SQL query
        party_name = getattr(t, 'party_name', 'Unknown')
        
        lines.append(
            f"ID={t.id} date={t.txn_date} party={party_name} qty={t.qty_liters} "
            f"fat={t.fat} snf={t.snf} rate={t.rate} amount={t.amount}"
        )

    return "<pre>" + "\n".join(lines) + "</pre>"

@milk_bp.route("/accounts/search")
@login_required
def search_accounts():
    """Search accounts for autocomplete"""
    cid = session.get("company_id")
    query = request.args.get("q", "").strip()
    
    if len(query) < 1:
        return jsonify({"success": False, "accounts": []})
    
    try:
        accounts = Account.query.filter(
            Account.company_id == cid,
            Account.is_active == True,
            Account.name.ilike(f"%{query}%")
        ).limit(20).all()
        
        account_data = []
        for account in accounts:
            account_data.append({
                "id": account.id,
                "name": account.name,
                "current_balance": 0.0,
                "balance_display": "Dr 0.00"
            })
        
        return jsonify({"success": True, "accounts": account_data})
        
    except Exception as e:
        print(f"Error in account search: {e}")
        return jsonify({"success": False, "accounts": []})

@milk_bp.route("/accounts/create", methods=["POST"])
@login_required
def create_account():
    """Create a new ledger account"""
    cid = session.get("company_id")
    
    try:
        name = request.form.get("name", "").strip()
        group_name = request.form.get("group_name", "").strip()
        opening_balance_str = request.form.get("opening_balance", "0")
        balance_type = request.form.get("balance_type", "Dr")
        account_type = request.form.get("account_type", "")
        
        # Fix opening balance conversion
        try:
            opening_balance = float(opening_balance_str) if opening_balance_str else 0.0
        except (ValueError, TypeError):
            opening_balance = 0.0
        
        if not name or not group_name:
            return jsonify({"success": False, "message": "Name and Group are required"})
        
        # Check if account already exists
        existing = Account.query.filter_by(company_id=cid, name=name).first()
        if existing:
            return jsonify({"success": False, "message": "Account with this name already exists"})
        
        # Create new account
        account = Account(
            company_id=cid,
            name=name,
            group_name=group_name,
            opening_dr=opening_balance if balance_type == "Dr" else 0,
            opening_cr=opening_balance if balance_type == "Cr" else 0,
            account_type=account_type if account_type else None,
            is_active=True
        )
        
        db.session.add(account)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "Account created successfully",
            "account": {
                "id": account.id,
                "name": account.name,
                "group_name": account.group_name
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating account: {e}")
        return jsonify({"success": False, "message": f"Error creating account: {str(e)}"})
