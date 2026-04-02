from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required
from extensions import db
from models import BankAccount, BankTransaction, BankImportLog, Party, Account, JournalHeader, JournalLine
from datetime import date, datetime
import hashlib, io, re, uuid

banking_bp = Blueprint("banking", __name__)

CASH_KEYWORDS   = ["CASH","CASH DEP","CASH WDL","ATM WDL","ATM CASH","BY CASH","TO CASH"]
SUSPENSE_KWORDS = ["UPI/","IMPS/","NEFT/","RTGS/","CHQ","CHEQUE","ECS","ACH"]
UPI_PATTERN     = re.compile(r"UPI[/-]", re.IGNORECASE)
CHQ_PATTERN     = re.compile(r"(CHQ|CHEQUE|CQ)[^\d]*(\d+)", re.IGNORECASE)

def detect_mode(desc):
    d = (desc or "").upper()
    if any(k in d for k in ["UPI","PHONEPE","GPAY","PAYTM","BHIM"]): return "UPI"
    if any(k in d for k in ["NEFT","RTGS"]): return d[:4]
    if any(k in d for k in ["IMPS"]): return "IMPS"
    if any(k in d for k in ["CHQ","CHEQUE","CQ"]): return "CHQ"
    if any(k in d for k in ["ECS","ACH","NACH"]): return "ECS"
    if any(k in d for k in ["ATM","CASH"]): return "CASH"
    if any(k in d for k in ["IFSC","TRANSFER"]): return "NEFT"
    return "OTHER"

def detect_ledger(desc, mode):
    d = (desc or "").upper()
    if mode == "CASH" or any(k in d for k in CASH_KEYWORDS): return "CASH"
    return "SUSPENSE"

def make_hash(bank_id, txn_date, debit, credit, ref_no, desc):
    raw = f"{bank_id}|{txn_date}|{debit}|{credit}|{ref_no}|{desc}"
    return hashlib.sha256(raw.encode()).hexdigest()

@banking_bp.route("/banking/accounts")
@login_required
def accounts():
    cid = session.get("company_id")
    banks = BankAccount.query.filter_by(company_id=cid, is_active=True).all()
    return render_template("banking/accounts.html", banks=banks)

@banking_bp.route("/banking/accounts/add", methods=["GET","POST"])
@login_required
def add_account():
    cid = session.get("company_id")
    if request.method == "POST":
        acc_no = request.form["account_no"].strip()
        acc_name = request.form["account_name"].strip()
        existing_no = BankAccount.query.filter_by(company_id=cid, account_no=acc_no).first()
        if existing_no:
            flash(f"❌ Account No {acc_no} already exists as '{existing_no.account_name}'", "danger")
            return redirect(url_for("banking.add_account"))
        existing_name = BankAccount.query.filter(
            BankAccount.company_id==cid,
            db.func.lower(BankAccount.account_name)==acc_name.lower()
        ).first()
        if existing_name:
            flash(f"❌ Account name '{acc_name}' already exists!", "danger")
            return redirect(url_for("banking.add_account"))
        b = BankAccount(
            company_id=cid,
            account_name=acc_name,
            bank_name=request.form["bank_name"].strip(),
            account_no=acc_no,
            ifsc=request.form.get("ifsc","").strip().upper(),
            branch=request.form.get("branch","").strip(),
            account_type=request.form.get("account_type","Current"),
            opening_balance=float(request.form.get("opening_balance") or 0)
        )
        db.session.add(b)
        db.session.flush()  # Get the bank account ID
        
        # Create corresponding ledger account for the bank
        from models import Account
        bank_account = Account(
            company_id=cid,
            name=f"{acc_name} - {request.form['bank_name'].strip()}",
            group_name="Bank Accounts",
            opening_dr=float(request.form.get("opening_balance") or 0),
            opening_cr=0,
            is_active=True
        )
        db.session.add(bank_account)
        db.session.flush()  # Get the ledger account ID
        
        # Link bank account to ledger account
        b.account_id = bank_account.id
        
        db.session.commit()
        
        flash(f"✅ Bank account '{acc_name}' created with ledger account!", "success")
        return redirect(url_for("banking.accounts"))
    return render_template("banking/account_form.html")

@banking_bp.route("/banking/template")
@login_required
def download_template():
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Bank Statement"
        headers = ["Date(DD/MM/YYYY)","Value Date","Description","Ref No / Cheque No","Debit","Credit","Balance"]
        ws.append(headers)
        from openpyxl.styles import Font, PatternFill
        for col, cell in enumerate(ws[1], 1):
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1a6b3a")
            ws.column_dimensions[cell.column_letter].width = 22
        ws.append(["23/03/2026","23/03/2026","UPI/123456/RAMESH DAIRY","UPI123456",0,5000,25000])
        ws.append(["23/03/2026","23/03/2026","CASH DEPOSIT","",10000,0,15000])
        ws.append(["23/03/2026","23/03/2026","CHQ NO 001234 SURESH KUMAR","001234",8000,0,7000])
        buf = io.BytesIO()
        wb.save(buf); buf.seek(0)
        return send_file(buf, download_name="bank_import_template.xlsx",
                        as_attachment=True, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        flash(f"Install openpyxl: pip install openpyxl | Error: {e}","danger")
        return redirect(url_for("banking.accounts"))

@banking_bp.route("/banking/import/<int:bank_id>", methods=["GET","POST"])
@login_required
def import_txns(bank_id):
    cid = session.get("company_id"); fy = session.get("fin_year")
    bank = BankAccount.query.filter_by(id=bank_id, company_id=cid).first_or_404()
    if request.method == "POST":
        try:
            import openpyxl
            f = request.files["file"]
            wb = openpyxl.load_workbook(f)
            ws = wb.active
            batch = str(uuid.uuid4())[:8]
            total = imported = dupes = errors = 0
            notes = []
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not any(row): continue
                total += 1
                try:
                    raw_date, val_date, desc, ref_no, debit, credit, balance = (row + (None,)*7)[:7]
                    if not raw_date: continue
                    if isinstance(raw_date, datetime): txn_date = raw_date.date()
                    elif isinstance(raw_date, date): txn_date = raw_date
                    else:
                        for fmt in ["%d/%m/%Y","%d-%m-%Y","%Y-%m-%d","%d/%m/%y"]:
                            try: txn_date = datetime.strptime(str(raw_date).strip(), fmt).date(); break
                            except: continue
                    debit  = float(debit  or 0)
                    credit = float(credit or 0)
                    balance= float(balance or 0)
                    ref_no = str(ref_no or "").strip()
                    desc   = str(desc or "").strip()
                    h = make_hash(bank_id, txn_date, debit, credit, ref_no, desc)
                    if BankTransaction.query.filter_by(hash_key=h).first():
                        dupes += 1; notes.append(f"DUP: {txn_date} {desc[:30]}"); continue
                    mode   = detect_mode(desc)
                    ledger = detect_ledger(desc, mode)
                    t = BankTransaction(
                        company_id=cid, fin_year=fy, bank_account_id=bank_id,
                        txn_date=txn_date,
                        value_date=val_date.date() if isinstance(val_date,datetime) else txn_date,
                        description=desc, ref_no=ref_no,
                        debit=debit, credit=credit, balance=balance,
                        txn_mode=mode, ledger_type=ledger,
                        import_batch=batch, hash_key=h
                    )
                    db.session.add(t); imported += 1
                except Exception as e:
                    errors += 1; notes.append(f"ERR row {total}: {e}")
            db.session.commit()
            log = BankImportLog(company_id=cid, bank_account_id=bank_id,
                file_name=f.filename, total_rows=total, imported=imported,
                duplicates=dupes, errors=errors, notes="\n".join(notes))
            db.session.add(log); db.session.commit()
            flash(f"✅ Imported {imported} | Duplicates skipped: {dupes} | Errors: {errors}", "success")
            return redirect(url_for("banking.transactions", bank_id=bank_id))
        except Exception as e:
            flash(f"❌ Import failed: {e}", "danger")
    return render_template("banking/import.html", bank=bank)

@banking_bp.route("/banking/transactions/<int:bank_id>")
@login_required
def transactions(bank_id):
    cid = session.get("company_id"); fy = session.get("fin_year")
    bank = BankAccount.query.filter_by(id=bank_id, company_id=cid).first_or_404()
    txns = BankTransaction.query.filter_by(
        bank_account_id=bank_id, company_id=cid, fin_year=fy
    ).order_by(BankTransaction.txn_date.desc()).limit(500).all()
    total_dr = sum(float(t.debit)  for t in txns)
    total_cr = sum(float(t.credit) for t in txns)
    suspense  = [t for t in txns if t.ledger_type=="SUSPENSE"]
    cash_txns = [t for t in txns if t.ledger_type=="CASH"]
    return render_template("banking/transactions.html",
        bank=bank, txns=txns, total_dr=total_dr, total_cr=total_cr,
        suspense_count=len(suspense), cash_count=len(cash_txns))

@banking_bp.route("/banking/entry/<int:bank_id>", methods=["GET","POST"])
@login_required
def manual_entry(bank_id):
    cid = session.get("company_id"); fy = session.get("fin_year")
    bank = BankAccount.query.filter_by(id=bank_id, company_id=cid).first_or_404()
    parties = Party.query.filter_by(company_id=cid, is_active=True).all()
    if request.method == "POST":
        desc = request.form["description"].strip()
        ref_no = request.form.get("ref_no","").strip()
        debit = float(request.form.get("debit") or 0)
        credit = float(request.form.get("credit") or 0)
        txn_date = datetime.strptime(request.form["txn_date"],"%Y-%m-%d").date()
        h = make_hash(bank_id, txn_date, debit, credit, ref_no, desc)
        if BankTransaction.query.filter_by(hash_key=h).first():
            flash("❌ Duplicate entry detected!", "danger")
            return redirect(url_for("banking.manual_entry", bank_id=bank_id))
        mode   = detect_mode(desc)
        ledger = detect_ledger(desc, mode)
        t = BankTransaction(
            company_id=cid, fin_year=fy, bank_account_id=bank_id,
            txn_date=txn_date, description=desc, ref_no=ref_no,
            debit=debit, credit=credit,
            txn_mode=mode, ledger_type=ledger, hash_key=h
        )
        db.session.add(t); db.session.commit()
        flash(f"✅ Entry saved → {ledger} Account ({mode})", "success")
        return redirect(url_for("banking.transactions", bank_id=bank_id))
    return render_template("banking/manual_entry.html", bank=bank, parties=parties, today=date.today().isoformat())

@banking_bp.route("/banking/quick-entry", methods=["GET","POST"])
@login_required
def quick_entry():
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    banks = BankAccount.query.filter_by(company_id=cid, is_active=True).all()
    accounts = Account.query.filter_by(company_id=cid, is_active=True).order_by(Account.name).all()
    
    # Calculate previous bank balances
    bank_balances = {}
    today = date.today()
    
    for bank in banks:
        # Get journal lines for this bank account up to today
        journal_lines = JournalLine.query.join(JournalHeader).filter(
            JournalHeader.company_id == cid,
            JournalLine.account_id == bank.account_id,
            JournalHeader.voucher_date <= today
        ).all()
        
        # Calculate balance: Debit - Credit
        balance = 0.0
        for line in journal_lines:
            balance += float(line.debit or 0)
            balance -= float(line.credit or 0)
        
        # Add opening balance if available
        if hasattr(bank, 'opening_balance') and bank.opening_balance:
            balance += float(bank.opening_balance)
        
        bank_balances[bank.id] = balance
    
    if request.method == "POST":
        bank_account_id = request.form.get("bank_account_id")
        transaction_type = request.form.get("transaction_type", "Deposit")
        payment_mode = request.form.get("payment_mode", "Cash")
        reference_no = request.form.get("reference_no", "").strip()
        party_name = request.form.get("party_name", "").strip()
        
        # Check if this is a single row save or batch save
        single_save = request.form.get("single_save") == "true"
        
        if single_save:
            # Single row save logic here...
            pass
        else:
            # Batch save logic here...
            pass
        
        return redirect(url_for("banking.accounts"))
    
    # Get default bank account
    default_bank = banks[0] if banks else None
    
    # Default date to last used or today
    default_date = session.get("last_txn_date") or date.today().isoformat()
    
    return render_template("banking/quick_entry.html", 
                         banks=banks,
                         accounts=accounts,
                         default_bank=default_bank,
                         today=default_date,
                         bank_balances=bank_balances)
