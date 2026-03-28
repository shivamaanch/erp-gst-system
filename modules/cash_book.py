from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from flask_login import login_required
from extensions import db
from models import CashBook, Company, FinancialYear, Account
from datetime import date, datetime
from sqlalchemy import text

cash_book_bp = Blueprint("cash_book", __name__)

def next_voucher_no(company_id, fin_year):
    """Generate next voucher number for cash book"""
    last = CashBook.query.filter_by(company_id=company_id, fin_year=fin_year).order_by(CashBook.id.desc()).first()
    if last and last.voucher_no:
        try:
            num = int(last.voucher_no.split('-')[-1]) + 1
        except:
            num = 1
    else:
        num = 1
    return f"CB-{fin_year}-{num:04d}"

@cash_book_bp.route("/cash-book")
@login_required
def index():
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Get filters
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    narration_filter = request.args.get("narration", "")
    
    # Build query
    query = CashBook.query.filter_by(company_id=cid, fin_year=fy)
    
    if from_date:
        query = query.filter(CashBook.transaction_date >= datetime.strptime(from_date, "%Y-%m-%d").date())
    if to_date:
        query = query.filter(CashBook.transaction_date <= datetime.strptime(to_date, "%Y-%m-%d").date())
    if narration_filter:
        query = query.filter(CashBook.narration.contains(narration_filter))
    
    transactions = query.order_by(CashBook.transaction_date.desc(), CashBook.id.desc()).all()
    
    # Calculate totals
    total_receipts = sum(t.amount for t in transactions if t.transaction_type == "Receipt")
    total_payments = sum(t.amount for t in transactions if t.transaction_type == "Payment")
    balance = total_receipts - total_payments
    
    return render_template("cash_book/index.html", 
                         transactions=transactions,
                         total_receipts=total_receipts,
                         total_payments=total_payments,
                         balance=balance,
                         from_date=from_date,
                         to_date=to_date,
                         narration_filter=narration_filter)

@cash_book_bp.route("/cash-book/add", methods=["GET", "POST"])
@login_required
def add():
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    if request.method == "POST":
        transaction_type = request.form["transaction_type"]
        amount = float(request.form["amount"])
        transaction_date = datetime.strptime(request.form["transaction_date"], "%Y-%m-%d").date()
        narration = request.form["narration"].strip()
        party_name = request.form.get("party_name", "").strip()
        payment_mode = request.form.get("payment_mode", "Cash")
        reference_no = request.form.get("reference_no", "").strip()
        
        # Generate voucher number
        voucher_no = next_voucher_no(cid, fy)
        
        # Create cash book entry
        entry = CashBook(
            company_id=cid,
            fin_year=fy,
            voucher_no=voucher_no,
            transaction_date=transaction_date,
            transaction_type=transaction_type,
            amount=amount,
            narration=narration,
            party_name=party_name,
            payment_mode=payment_mode,
            reference_no=reference_no
        )
        db.session.add(entry)
        db.session.commit()
        
        flash(f"Cash book entry {voucher_no} added successfully!", "success")
        return redirect(url_for("cash_book.index"))
    
    # Generate next voucher number for display
    next_voucher = next_voucher_no(cid, fy)
    return render_template("cash_book/form.html", 
                         entry=None,
                         next_voucher=next_voucher,
                         today=date.today().isoformat())

@cash_book_bp.route("/cash-book/edit/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit(entry_id):
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    entry = CashBook.query.filter_by(id=entry_id, company_id=cid, fin_year=fy).first_or_404()
    
    if request.method == "POST":
        entry.transaction_type = request.form["transaction_type"]
        entry.amount = float(request.form["amount"])
        entry.transaction_date = datetime.strptime(request.form["transaction_date"], "%Y-%m-%d").date()
        entry.narration = request.form["narration"].strip()
        entry.party_name = request.form.get("party_name", "").strip()
        entry.payment_mode = request.form.get("payment_mode", "Cash")
        entry.reference_no = request.form.get("reference_no", "").strip()
        
        db.session.commit()
        flash(f"Cash book entry {entry.voucher_no} updated successfully!", "success")
        return redirect(url_for("cash_book.index"))
    
    return render_template("cash_book/form.html", 
                         entry=entry,
                         next_voucher=entry.voucher_no,
                         today=entry.transaction_date.isoformat())

@cash_book_bp.route("/cash-book/delete/<int:entry_id>", methods=["POST"])
@login_required
def delete(entry_id):
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    entry = CashBook.query.filter_by(id=entry_id, company_id=cid, fin_year=fy).first_or_404()
    voucher_no = entry.voucher_no
    
    db.session.delete(entry)
    db.session.commit()
    
    flash(f"Cash book entry {voucher_no} deleted successfully!", "success")
    return redirect(url_for("cash_book.index"))

@cash_book_bp.route("/cash-book/view/<int:entry_id>")
@login_required
def view(entry_id):
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    entry = CashBook.query.filter_by(id=entry_id, company_id=cid, fin_year=fy).first_or_404()
    
    return render_template("cash_book/view.html", entry=entry)

@cash_book_bp.route("/cash-book/quick-entry", methods=["GET", "POST"])
@login_required
def quick_entry():
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    if request.method == "POST":
        transaction_date = datetime.strptime(request.form["transaction_date"], "%Y-%m-%d").date()
        payment_mode = request.form.get("payment_mode", "Cash")
        reference_no = request.form.get("reference_no", "").strip()
        
        # Get all form arrays
        account_ids = request.form.getlist("account_id[]")
        transaction_types = request.form.getlist("transaction_type[]")
        amounts = request.form.getlist("amount[]")
        narrations = request.form.getlist("narration[]")
        
        entries_created = 0
        for i in range(len(account_ids)):
            if not account_ids[i] or not transaction_types[i] or not amounts[i] or not narrations[i]:
                continue
            
            # Generate voucher number for each entry
            voucher_no = next_voucher_no(cid, fy)
            
            # Get account name for party_name field
            account = Account.query.get(account_ids[i])
            party_name = account.name if account else ""
            
            entry = CashBook(
                company_id=cid,
                fin_year=fy,
                voucher_no=voucher_no,
                transaction_date=transaction_date,
                transaction_type=transaction_types[i],
                amount=float(amounts[i]),
                narration=narrations[i],
                party_name=party_name,
                payment_mode=payment_mode,
                reference_no=reference_no
            )
            db.session.add(entry)
            entries_created += 1
        
        if entries_created > 0:
            db.session.commit()
            flash(f"{entries_created} cash book entries created successfully!", "success")
        else:
            flash("No valid entries to save", "warning")
        
        return redirect(url_for("cash_book.index"))
    
    # Get accounts for dropdown
    accounts = Account.query.filter_by(company_id=cid, is_active=True).order_by(Account.name).all()
    return render_template("cash_book/quick_entry.html", 
                         accounts=accounts,
                         today=date.today().isoformat())
