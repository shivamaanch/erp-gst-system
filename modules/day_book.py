from flask import Blueprint, render_template, request, session, flash, redirect, url_for, make_response
from flask_login import login_required
from extensions import db
from models import DayBook, Account, Company, Bill, MilkTransaction, Party, JournalHeader, JournalLine, CashBook
from datetime import date, datetime
from sqlalchemy import text, or_, and_
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
    
    # Collect all transactions from ALL sources
    transactions = []
    seen_vouchers = set()  # Track voucher numbers to avoid duplicates
    
    # 1. Journal Entries (includes auto-posted from cash book)
    jh_query = JournalHeader.query.filter_by(company_id=cid, fin_year=fy, is_cancelled=False)
    if from_date:
        jh_query = jh_query.filter(JournalHeader.voucher_date >= datetime.strptime(from_date, "%Y-%m-%d").date())
    if to_date:
        jh_query = jh_query.filter(JournalHeader.voucher_date <= datetime.strptime(to_date, "%Y-%m-%d").date())
    if search:
        jh_query = jh_query.filter(or_(
            JournalHeader.narration.ilike(f"%{search}%"),
            JournalHeader.voucher_no.ilike(f"%{search}%")
        ))
    
    for jh in jh_query.all():
        lines = JournalLine.query.filter_by(journal_header_id=jh.id).all()
        for line in lines:
            account = Account.query.get(line.account_id) if line.account_id else None
            acc_name = account.name if account else 'Unknown'
            debit = float(line.debit or 0)
            credit = float(line.credit or 0)
            
            if account_filter and str(line.account_id) != str(account_filter):
                continue
            if search and search.lower() not in (jh.narration or '').lower() and search.lower() not in acc_name.lower():
                continue
            
            vtype = jh.voucher_type or 'Journal'
            transactions.append({
                'type': vtype,
                'date': jh.voucher_date,
                'voucher_no': jh.voucher_no,
                'account': acc_name,
                'debit': debit,
                'credit': credit,
                'narration': line.narration or jh.narration or '',
                'id': jh.id,
                'edit_url': url_for('journal.view', jh_id=jh.id),
                'delete_url': '#'
            })
        seen_vouchers.add(jh.voucher_no)
    
    # 2. Bills (Sales/Purchase invoices including milk)
    bills_query = Bill.query.filter_by(company_id=cid, fin_year=fy, is_cancelled=False)
    if search:
        bills_query = bills_query.filter(or_(
            Bill.narration.ilike(f"%{search}%"),
            Bill.bill_no.ilike(f"%{search}%")
        ))
    if from_date:
        bills_query = bills_query.filter(Bill.bill_date >= datetime.strptime(from_date, "%Y-%m-%d").date())
    if to_date:
        bills_query = bills_query.filter(Bill.bill_date <= datetime.strptime(to_date, "%Y-%m-%d").date())
    
    for bill in bills_query.all():
        if bill.bill_no in seen_vouchers:
            continue
        party = Party.query.get(bill.party_id) if bill.party_id else None
        acc_name = party.name if party else 'Unknown Party'
        if account_filter:
            # Check if party has matching account
            matching_acc = Account.query.filter_by(company_id=cid, id=int(account_filter)).first()
            if matching_acc and matching_acc.name.lower() != acc_name.lower():
                continue
        
        amt = float(bill.total_amount or 0)
        transactions.append({
            'type': bill.bill_type or 'Invoice',
            'date': bill.bill_date or date.today(),
            'voucher_no': bill.bill_no or f'BILL-{bill.id}',
            'account': acc_name,
            'debit': amt if bill.bill_type == 'Purchase' else 0,
            'credit': amt if bill.bill_type in ('Sales', 'Sale') else 0,
            'narration': bill.narration or f'{bill.bill_type} #{bill.bill_no}',
            'id': bill.id,
            'edit_url': url_for('enhanced_invoice.print_invoice', bill_id=bill.id) if bill.bill_type in ('Sales', 'Sale') else '#',
            'delete_url': '#'
        })
        seen_vouchers.add(bill.bill_no)
    
    # 3. Cash Book entries NOT already in journals (legacy entries without journal posting)
    cb_query = CashBook.query.filter_by(company_id=cid, fin_year=fy)
    if from_date:
        cb_query = cb_query.filter(CashBook.transaction_date >= datetime.strptime(from_date, "%Y-%m-%d").date())
    if to_date:
        cb_query = cb_query.filter(CashBook.transaction_date <= datetime.strptime(to_date, "%Y-%m-%d").date())
    if search:
        cb_query = cb_query.filter(or_(
            CashBook.narration.ilike(f"%{search}%"),
            CashBook.party_name.ilike(f"%{search}%")
        ))
    
    for cb in cb_query.all():
        if cb.voucher_no in seen_vouchers:
            continue
        # Check if this CB entry has a corresponding journal entry
        has_journal = JournalHeader.query.filter(
            JournalHeader.company_id == cid,
            JournalHeader.narration.ilike(f"%{cb.voucher_no}%")
        ).first()
        if has_journal:
            continue  # Already shown via journal entries
        
        acc_name = cb.party_name or 'Cash'
        if account_filter:
            if cb.account_id and str(cb.account_id) != str(account_filter):
                continue
        
        amt = float(cb.amount or 0)
        transactions.append({
            'type': 'Cash ' + (cb.transaction_type or ''),
            'date': cb.transaction_date,
            'voucher_no': cb.voucher_no,
            'account': acc_name,
            'debit': amt if cb.transaction_type == 'Payment' else 0,
            'credit': amt if cb.transaction_type == 'Receipt' else 0,
            'narration': cb.narration or '',
            'id': cb.id,
            'edit_url': url_for('cash_book.edit', entry_id=cb.id),
            'delete_url': '#'
        })
    
    # Sort all transactions by date (newest first)
    transactions.sort(key=lambda x: x['date'], reverse=True)
    
    # Calculate totals
    total_debit = sum(float(t['debit'] or 0) for t in transactions)
    total_credit = sum(float(t['credit'] or 0) for t in transactions)
    balance = total_debit - total_credit
    
    # Get accounts for filter dropdown
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

def _collect_all_transactions(cid, fy, search="", from_date=None, to_date=None, account_filter=""):
    """Collect ALL transactions from journals, bills, cash book for day book display/export."""
    transactions = []
    seen_vouchers = set()

    # 1. Journal Entries
    jh_query = JournalHeader.query.filter_by(company_id=cid, fin_year=fy, is_cancelled=False)
    if from_date:
        jh_query = jh_query.filter(JournalHeader.voucher_date >= datetime.strptime(from_date, "%Y-%m-%d").date())
    if to_date:
        jh_query = jh_query.filter(JournalHeader.voucher_date <= datetime.strptime(to_date, "%Y-%m-%d").date())
    if search:
        jh_query = jh_query.filter(or_(JournalHeader.narration.ilike(f"%{search}%"), JournalHeader.voucher_no.ilike(f"%{search}%")))

    for jh in jh_query.all():
        for line in JournalLine.query.filter_by(journal_header_id=jh.id).all():
            account = Account.query.get(line.account_id) if line.account_id else None
            acc_name = account.name if account else 'Unknown'
            if account_filter and str(line.account_id) != str(account_filter):
                continue
            transactions.append({
                'type': jh.voucher_type or 'Journal', 'date': jh.voucher_date,
                'voucher_no': jh.voucher_no, 'account': acc_name,
                'debit': float(line.debit or 0), 'credit': float(line.credit or 0),
                'narration': line.narration or jh.narration or ''
            })
        seen_vouchers.add(jh.voucher_no)

    # 2. Bills
    bills_query = Bill.query.filter_by(company_id=cid, fin_year=fy, is_cancelled=False)
    if search:
        bills_query = bills_query.filter(or_(Bill.narration.ilike(f"%{search}%"), Bill.bill_no.ilike(f"%{search}%")))
    if from_date:
        bills_query = bills_query.filter(Bill.bill_date >= datetime.strptime(from_date, "%Y-%m-%d").date())
    if to_date:
        bills_query = bills_query.filter(Bill.bill_date <= datetime.strptime(to_date, "%Y-%m-%d").date())

    for bill in bills_query.all():
        if bill.bill_no in seen_vouchers:
            continue
        party = Party.query.get(bill.party_id) if bill.party_id else None
        amt = float(bill.total_amount or 0)
        transactions.append({
            'type': bill.bill_type or 'Invoice', 'date': bill.bill_date or date.today(),
            'voucher_no': bill.bill_no or f'BILL-{bill.id}',
            'account': party.name if party else 'Unknown Party',
            'debit': amt if bill.bill_type == 'Purchase' else 0,
            'credit': amt if bill.bill_type in ('Sales', 'Sale') else 0,
            'narration': bill.narration or f'{bill.bill_type} #{bill.bill_no}'
        })
        seen_vouchers.add(bill.bill_no)

    # 3. Legacy cash book entries not in journals
    cb_query = CashBook.query.filter_by(company_id=cid, fin_year=fy)
    if from_date:
        cb_query = cb_query.filter(CashBook.transaction_date >= datetime.strptime(from_date, "%Y-%m-%d").date())
    if to_date:
        cb_query = cb_query.filter(CashBook.transaction_date <= datetime.strptime(to_date, "%Y-%m-%d").date())
    if search:
        cb_query = cb_query.filter(or_(CashBook.narration.ilike(f"%{search}%"), CashBook.party_name.ilike(f"%{search}%")))

    for cb in cb_query.all():
        if cb.voucher_no in seen_vouchers:
            continue
        has_journal = JournalHeader.query.filter(JournalHeader.company_id == cid, JournalHeader.narration.ilike(f"%{cb.voucher_no}%")).first()
        if has_journal:
            continue
        amt = float(cb.amount or 0)
        transactions.append({
            'type': 'Cash ' + (cb.transaction_type or ''), 'date': cb.transaction_date,
            'voucher_no': cb.voucher_no, 'account': cb.party_name or 'Cash',
            'debit': amt if cb.transaction_type == 'Payment' else 0,
            'credit': amt if cb.transaction_type == 'Receipt' else 0,
            'narration': cb.narration or ''
        })

    transactions.sort(key=lambda x: x['date'], reverse=True)
    return transactions

@day_book_bp.route("/day-book/export/<format>")
@login_required
def export(format):
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    search = request.args.get("search", "")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    account_filter = request.args.get("account_id", "")
    
    transactions = _collect_all_transactions(cid, fy, search, from_date, to_date, account_filter)
    
    if format == "excel":
        output = io.StringIO()
        writer = csv.writer(output)
        
        company = Company.query.get(cid)
        writer.writerow([company.name if company else 'Company'])
        writer.writerow([f'Day Book - FY: {fy}'])
        writer.writerow([])
        writer.writerow(['Type', 'Voucher No', 'Date', 'Account', 'Debit', 'Credit', 'Narration'])
        
        for t in transactions:
            writer.writerow([
                t['type'], t['voucher_no'],
                t['date'].strftime('%d-%m-%Y') if t['date'] else '',
                t['account'], t['debit'], t['credit'], t['narration']
            ])
        
        writer.writerow([])
        writer.writerow(['', '', '', 'TOTAL',
            sum(float(t['debit'] or 0) for t in transactions),
            sum(float(t['credit'] or 0) for t in transactions), ''])
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=day_book_{date.today()}.csv'
        response.headers['Content-type'] = 'text/csv'
        return response
    
    elif format == "pdf":
        company = Company.query.get(cid)
        return render_template("day_book/pdf.html", 
                             transactions=transactions,
                             company=company,
                             search=search,
                             from_date=from_date,
                             to_date=to_date,
                             account_filter=account_filter)
    
    return redirect(url_for("day_book.index"))
