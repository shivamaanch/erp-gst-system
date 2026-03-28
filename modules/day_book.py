from flask import Blueprint, render_template, request, session, flash, redirect, url_for, make_response
from flask_login import login_required
from extensions import db
from models import DayBook, Account, Company
from datetime import date, datetime
from sqlalchemy import text
import csv
import io

day_book_bp = Blueprint("day_book", __name__)

def next_voucher_no(company_id, fin_year):
    """Generate next voucher number for day book"""
    last = DayBook.query.filter_by(company_id=company_id, fin_year=fin_year).order_by(DayBook.id.desc()).first()
    if last and last.voucher_no:
        try:
            num = int(last.voucher_no.split('-')[-1]) + 1
        except:
            num = 1
    else:
        num = 1
    return f"DB-{fin_year}-{num:04d}"

@day_book_bp.route("/day-book")
@login_required
def index():
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Get filters
    search = request.args.get("search", "")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    account_filter = request.args.get("account_id", "")
    
    # Build query
    query = DayBook.query.filter_by(company_id=cid, fin_year=fy)
    
    if search:
        query = query.filter(DayBook.narration.contains(search))
    if from_date:
        query = query.filter(DayBook.transaction_date >= datetime.strptime(from_date, "%Y-%m-%d").date())
    if to_date:
        query = query.filter(DayBook.transaction_date <= datetime.strptime(to_date, "%Y-%m-%d").date())
    if account_filter:
        query = query.filter(DayBook.account_id == int(account_filter))
    
    transactions = query.order_by(DayBook.transaction_date.desc()).all()
    
    # Calculate totals
    total_debit = sum(t.debit_amount for t in transactions)
    total_credit = sum(t.credit_amount for t in transactions)
    balance = total_debit - total_credit
    
    # Get accounts for filter
    accounts = Account.query.filter_by(company_id=cid, is_active=True).order_by(Account.name).all()
    
    return render_template("day_book/index.html", 
                         transactions=transactions,
                         total_debit=total_debit,
                         total_credit=total_credit,
                         balance=balance,
                         accounts=accounts,
                         search=search,
                         from_date=from_date,
                         to_date=to_date,
                         account_filter=account_filter)

@day_book_bp.route("/day-book/add", methods=["GET", "POST"])
@login_required
def add():
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    if request.method == "POST":
        account_id = request.form["account_id"]
        transaction_date = datetime.strptime(request.form["transaction_date"], "%Y-%m-%d").date()
        debit_amount = float(request.form.get("debit_amount", 0))
        credit_amount = float(request.form.get("credit_amount", 0))
        narration = request.form["narration"].strip()
        
        # Generate voucher number
        voucher_no = next_voucher_no(cid, fy)
        
        # Create day book entry
        entry = DayBook(
            company_id=cid,
            fin_year=fy,
            voucher_no=voucher_no,
            transaction_date=transaction_date,
            account_id=account_id,
            debit_amount=debit_amount,
            credit_amount=credit_amount,
            narration=narration
        )
        db.session.add(entry)
        db.session.commit()
        
        flash(f"Day book entry {voucher_no} added successfully!", "success")
        return redirect(url_for("day_book.index"))
    
    # Get accounts for dropdown
    accounts = Account.query.filter_by(company_id=cid, is_active=True).order_by(Account.name).all()
    return render_template("day_book/form.html", 
                         entry=None,
                         next_voucher=next_voucher_no(cid, fy),
                         today=date.today().isoformat(),
                         accounts=accounts)

@day_book_bp.route("/day-book/edit/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit(entry_id):
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    entry = DayBook.query.filter_by(id=entry_id, company_id=cid, fin_year=fy).first_or_404()
    
    if request.method == "POST":
        entry.account_id = request.form["account_id"]
        entry.transaction_date = datetime.strptime(request.form["transaction_date"], "%Y-%m-%d").date()
        entry.debit_amount = float(request.form.get("debit_amount", 0))
        entry.credit_amount = float(request.form.get("credit_amount", 0))
        entry.narration = request.form["narration"].strip()
        
        db.session.commit()
        flash(f"Day book entry {entry.voucher_no} updated successfully!", "success")
        return redirect(url_for("day_book.index"))
    
    accounts = Account.query.filter_by(company_id=cid, is_active=True).order_by(Account.name).all()
    return render_template("day_book/form.html", 
                         entry=entry,
                         next_voucher=entry.voucher_no,
                         today=entry.transaction_date.isoformat(),
                         accounts=accounts)

@day_book_bp.route("/day-book/delete/<int:entry_id>", methods=["POST"])
@login_required
def delete(entry_id):
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    entry = DayBook.query.filter_by(id=entry_id, company_id=cid, fin_year=fy).first_or_404()
    voucher_no = entry.voucher_no
    
    db.session.delete(entry)
    db.session.commit()
    
    flash(f"Day book entry {voucher_no} deleted successfully!", "success")
    return redirect(url_for("day_book.index"))

@day_book_bp.route("/day-book/view/<int:entry_id>")
@login_required
def view(entry_id):
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    entry = DayBook.query.filter_by(id=entry_id, company_id=cid, fin_year=fy).first_or_404()
    
    return render_template("day_book/view.html", entry=entry)

@day_book_bp.route("/day-book/export/<format>")
@login_required
def export(format):
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Get filtered data
    search = request.args.get("search", "")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    account_filter = request.args.get("account_id", "")
    
    query = DayBook.query.filter_by(company_id=cid, fin_year=fy)
    
    if search:
        query = query.filter(DayBook.narration.contains(search))
    if from_date:
        query = query.filter(DayBook.transaction_date >= datetime.strptime(from_date, "%Y-%m-%d").date())
    if to_date:
        query = query.filter(DayBook.transaction_date <= datetime.strptime(to_date, "%Y-%m-%d").date())
    if account_filter:
        query = query.filter(DayBook.account_id == int(account_filter))
    
    transactions = query.order_by(DayBook.transaction_date.desc()).all()
    
    if format == "excel":
        # Create CSV for Excel
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Voucher No', 'Date', 'Account', 'Debit', 'Credit', 'Narration'])
        
        # Data
        for t in transactions:
            writer.writerow([
                t.voucher_no,
                t.transaction_date.strftime('%d-%m-%Y'),
                t.account.name if t.account else '',
                t.debit_amount,
                t.credit_amount,
                t.narration
            ])
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=day_book_{date.today()}.csv'
        response.headers['Content-type'] = 'text/csv'
        return response
    
    elif format == "pdf":
        # Return PDF template
        company = Company.query.get(cid)
        return render_template("day_book/pdf.html", 
                             transactions=transactions,
                             company=company,
                             search=search,
                             from_date=from_date,
                             to_date=to_date,
                             account_filter=account_filter)
    
    return redirect(url_for("day_book.index"))
