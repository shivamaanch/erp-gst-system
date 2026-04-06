from flask import Blueprint, render_template, request, session, jsonify
from flask_login import login_required
from extensions import db
from sqlalchemy import func
from models import Account, Party, JournalHeader, JournalLine, MilkTransaction, Bill, CashBook, Company
from utils.filters import fy_dates
import re

reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/reports")
@reports_bp.route("/reports/hub")
@login_required
def hub():
    """Reports hub - main reports dashboard"""
    from datetime import date
    
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Get some basic stats for the dashboard
    from sqlalchemy import text
    
    # Get account count
    account_count = Account.query.filter_by(company_id=cid, is_active=True).count()
    
    # Get party count
    party_count = Party.query.filter_by(company_id=cid, is_active=True).count()
    
    # Get transaction count
    start, end = fy_dates(fy)
    transaction_count = db.session.query(JournalHeader).filter(
        JournalHeader.company_id == cid,
        JournalHeader.voucher_date >= start,
        JournalHeader.voucher_date <= end,
        JournalHeader.is_cancelled == False
    ).count()
    
    # Calculate total sales and purchases
    total_sales = 0.0
    total_purchases = 0.0
    
    # Get sales accounts (income accounts)
    sales_accounts = Account.query.filter(
        Account.company_id == cid,
        Account.group_name.like('%Income%'),
        Account.is_active == True
    ).all()
    
    for account in sales_accounts:
        bal_query = db.session.query(
            func.sum(JournalLine.credit) - func.sum(JournalLine.debit)
        ).join(JournalHeader).filter(
            JournalLine.account_id == account.id,
            JournalHeader.company_id == cid,
            JournalHeader.voucher_date >= start,
            JournalHeader.voucher_date <= end
        ).scalar()
        total_sales += float(bal_query or 0)
    
    # Get purchase accounts (expense accounts)
    purchase_accounts = Account.query.filter(
        Account.company_id == cid,
        Account.group_name.like('%Expense%'),
        Account.is_active == True
    ).all()
    
    for account in purchase_accounts:
        bal_query = db.session.query(
            func.sum(JournalLine.debit) - func.sum(JournalLine.credit)
        ).join(JournalHeader).filter(
            JournalLine.account_id == account.id,
            JournalHeader.company_id == cid,
            JournalHeader.voucher_date >= start,
            JournalHeader.voucher_date <= end
        ).scalar()
        total_purchases += float(bal_query or 0)
    
    # Calculate net profit
    net_profit = total_sales - total_purchases
    
    # Calculate financial position (total assets - total liabilities)
    financial_position = 0.0
    
    # Get all account balances for financial position
    account_balances = db.session.query(
        Account.id,
        Account.name,
        Account.group_name,
        Account.opening_dr,
        Account.opening_cr,
        func.sum(JournalLine.debit).label("dr"),
        func.sum(JournalLine.credit).label("cr"),
    ).join(JournalLine, JournalLine.account_id == Account.id
    ).join(JournalHeader, JournalHeader.id == JournalLine.journal_header_id
    ).filter(
        Account.company_id == cid,
        JournalHeader.company_id == cid,
        JournalHeader.voucher_date >= start,
        JournalHeader.voucher_date <= end,
        JournalHeader.is_cancelled == False,
        Account.is_active == True
    ).group_by(Account.id, Account.name, Account.group_name, Account.opening_dr, Account.opening_cr).all()
    
    for acc in account_balances:
        balance = float(acc.dr or 0) - float(acc.cr or 0)
        opening_balance = float(acc.opening_dr or 0) - float(acc.opening_cr or 0)
        balance += opening_balance
        
        financial_position += balance
    
    # Generate month options for period selection
    from datetime import datetime, timedelta
    month_options = []
    current_period = request.args.get('period', date.today().strftime('%m-%Y'))
    
    # Generate last 12 months
    for i in range(12):
        month_date = date.today().replace(day=1) - timedelta(days=30*i)
        month_str = month_date.strftime('%m-%Y')
        month_label = month_date.strftime('%B %Y')
        selected = month_str == current_period
        month_options.append((month_str, month_label, selected))
    
    return render_template("reports/hub.html", 
                         account_count=account_count,
                         party_count=party_count,
                         transaction_count=transaction_count,
                         total_sales=total_sales,
                         total_purchases=total_purchases,
                         net_profit=net_profit,
                         financial_position=financial_position,
                         month_options=month_options,
                         fy=fy,
                         current_date=date.today())

@reports_bp.route("/reports/profit-loss")
@login_required
def profit_loss():
    """Profit & Loss report"""
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Basic P&L calculation
    start, end = fy_dates(fy)
    
    # Get income and expense accounts
    income_accounts = Account.query.filter(
        Account.company_id == cid,
        Account.group_name.like('%Income%'),
        Account.is_active == True
    ).all()
    
    expense_accounts = Account.query.filter(
        Account.company_id == cid,
        Account.group_name.like('%Expense%'),
        Account.is_active == True
    ).all()
    
    # Calculate totals
    total_income = 0.0
    total_expense = 0.0
    
    for account in income_accounts:
        # Get balance for income accounts (credit balance)
        bal_query = db.session.query(
            func.sum(JournalLine.credit) - func.sum(JournalLine.debit)
        ).join(JournalHeader).filter(
            JournalLine.account_id == account.id,
            JournalHeader.company_id == cid,
            JournalHeader.voucher_date >= start,
            JournalHeader.voucher_date <= end
        ).scalar()
        total_income += float(bal_query or 0)
    
    for account in expense_accounts:
        # Get balance for expense accounts (debit balance)
        bal_query = db.session.query(
            func.sum(JournalLine.debit) - func.sum(JournalLine.credit)
        ).join(JournalHeader).filter(
            JournalLine.account_id == account.id,
            JournalHeader.company_id == cid,
            JournalHeader.voucher_date >= start,
            JournalHeader.voucher_date <= end
        ).scalar()
        total_expense += float(bal_query or 0)
    
    net_profit = total_income - total_expense
    
    return render_template("reports/profit_loss.html",
                         total_income=total_income,
                         total_expense=total_expense,
                         net_profit=net_profit,
                         fy=fy)

@reports_bp.route("/reports/balance-sheet")
@login_required
def balance_sheet():
    """Balance Sheet report"""
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Basic balance sheet calculation
    start, end = fy_dates(fy)
    
    # Get asset and liability accounts
    asset_accounts = Account.query.filter(
        Account.company_id == cid,
        Account.group_name.like('%Asset%'),
        Account.is_active == True
    ).all()
    
    liability_accounts = Account.query.filter(
        Account.company_id == cid,
        Account.group_name.like('%Liability%'),
        Account.is_active == True
    ).all()
    
    equity_accounts = Account.query.filter(
        Account.company_id == cid,
        Account.group_name.like('%Equity%'),
        Account.is_active == True
    ).all()
    
    # Calculate totals
    total_assets = 0.0
    total_liabilities = 0.0
    total_equity = 0.0
    
    for account in asset_accounts:
        # Get balance for asset accounts (debit balance)
        bal_query = db.session.query(
            func.sum(JournalLine.debit) - func.sum(JournalLine.credit)
        ).join(JournalHeader).filter(
            JournalLine.account_id == account.id,
            JournalHeader.company_id == cid,
            JournalHeader.voucher_date >= start,
            JournalHeader.voucher_date <= end
        ).scalar()
        total_assets += float(bal_query or 0)
    
    for account in liability_accounts:
        # Get balance for liability accounts (credit balance)
        bal_query = db.session.query(
            func.sum(JournalLine.credit) - func.sum(JournalLine.debit)
        ).join(JournalHeader).filter(
            JournalLine.account_id == account.id,
            JournalHeader.company_id == cid,
            JournalHeader.voucher_date >= start,
            JournalHeader.voucher_date <= end
        ).scalar()
        total_liabilities += float(bal_query or 0)
    
    for account in equity_accounts:
        # Get balance for equity accounts (credit balance)
        bal_query = db.session.query(
            func.sum(JournalLine.credit) - func.sum(JournalLine.debit)
        ).join(JournalHeader).filter(
            JournalLine.account_id == account.id,
            JournalHeader.company_id == cid,
            JournalHeader.voucher_date >= start,
            JournalHeader.voucher_date <= end
        ).scalar()
        total_equity += float(bal_query or 0)
    
    return render_template("reports/balance_sheet.html",
                         total_assets=total_assets,
                         total_liabilities=total_liabilities,
                         total_equity=total_equity,
                         fy=fy)

@reports_bp.route("/reports/trial-balance")
@login_required
def trial_balance():
    """Trial Balance report"""
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    start, end = fy_dates(fy)
    
    # Get all active accounts
    accounts = Account.query.filter_by(company_id=cid, is_active=True).order_by(Account.name).all()
    
    trial_balance_data = []
    total_debits = 0.0
    total_credits = 0.0
    
    for account in accounts:
        # Get debit and credit totals for this account
        debits_query = db.session.query(func.sum(JournalLine.debit)).join(JournalHeader).filter(
            JournalLine.account_id == account.id,
            JournalHeader.company_id == cid,
            JournalHeader.voucher_date >= start,
            JournalHeader.voucher_date <= end
        ).scalar() or 0.0
        
        credits_query = db.session.query(func.sum(JournalLine.credit)).join(JournalHeader).filter(
            JournalLine.account_id == account.id,
            JournalHeader.company_id == cid,
            JournalHeader.voucher_date >= start,
            JournalHeader.voucher_date <= end
        ).scalar() or 0.0
        
        debits = float(debits_query)
        credits = float(credits_query)
        
        # Only include accounts with activity
        if debits > 0 or credits > 0:
            trial_balance_data.append({
                'account_name': account.name,
                'group_name': account.group_name,
                'debits': debits,
                'credits': credits
            })
            total_debits += debits
            total_credits += credits
    
    return render_template("reports/trial_balance.html",
                         trial_balance_data=trial_balance_data,
                         total_debits=total_debits,
                         total_credits=total_credits,
                         fy=fy)

@reports_bp.route("/reports/account-ledger/<int:account_id>/pdf")
@login_required
def account_ledger_pdf(account_id):
    """Generate PDF for account ledger"""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch, cm
    from io import BytesIO
    from flask import Response
    
    cid = session.get("company_id")
    fy = session.get("fin_year")
    company = Company.query.get(cid)
    
    # Get account details
    account = Account.query.filter_by(id=account_id, company_id=cid).first()
    if not account:
        return "Account not found", 404
    
    # Get transactions (reuse logic from account_ledger)
    start, end = fy_dates(fy)
    transactions = db.session.query(
        JournalLine,
        JournalHeader
    ).join(JournalHeader, JournalHeader.id == JournalLine.journal_header_id
    ).filter(
        JournalLine.account_id == account_id,
        JournalHeader.company_id == cid,
        JournalHeader.voucher_date >= start,
        JournalHeader.voucher_date <= end,
        JournalHeader.is_cancelled == False
    ).order_by(JournalHeader.voucher_date, JournalHeader.id).all()
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                             leftMargin=0.5*inch, rightMargin=0.5*inch,
                             topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                 fontSize=16, alignment=1, spaceAfter=12)
    elements.append(Paragraph(f"Account Ledger - {account.name}", title_style))
    elements.append(Paragraph(f"Financial Year: {fy}", styles['Normal']))
    elements.append(Paragraph(f"Company: {company.name if company else 'N/A'}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Table data
    data = [['Date', 'Voucher No', 'Narration', 'Debit', 'Credit', 'Balance']]
    
    running_balance = float(account.opening_dr or 0) - float(account.opening_cr or 0)
    
    for line, header in transactions:
        debit = float(line.debit or 0)
        credit = float(line.credit or 0)
        
        if debit > 0:
            running_balance += debit
        else:
            running_balance -= credit
        
        data.append([
            header.voucher_date.strftime('%d-%m-%Y'),
            header.voucher_no,
            (line.narration or header.narration)[:50],
            f"₹{debit:,.2f}" if debit > 0 else '',
            f"₹{credit:,.2f}" if credit > 0 else '',
            f"₹{running_balance:,.2f}"
        ])
    
    # Create table
    table = Table(data, colWidths=[1*cm, 2*cm, 8*cm, 2*cm, 2*cm, 2*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    # Return PDF
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    
    filename = f"account_ledger_{account.name}_{fy}.pdf"
    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@reports_bp.route("/reports/account-ledger/<int:account_id>/excel")
@login_required
def account_ledger_excel(account_id):
    """Generate Excel for account ledger"""
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from io import BytesIO
    
    cid = session.get("company_id")
    fy = session.get("fin_year")
    company = Company.query.get(cid)
    
    # Get account details
    account = Account.query.filter_by(id=account_id, company_id=cid).first()
    if not account:
        return "Account not found", 404
    
    # Get transactions (reuse logic from account_ledger)
    start, end = fy_dates(fy)
    transactions = db.session.query(
        JournalLine,
        JournalHeader
    ).join(JournalHeader, JournalHeader.id == JournalLine.journal_header_id
    ).filter(
        JournalLine.account_id == account_id,
        JournalHeader.company_id == cid,
        JournalHeader.voucher_date >= start,
        JournalHeader.voucher_date <= end,
        JournalHeader.is_cancelled == False
    ).order_by(JournalHeader.voucher_date, JournalHeader.id).all()
    
    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Account Ledger"
    
    # Headers
    headers = ['Date', 'Voucher No', 'Narration', 'Debit', 'Credit', 'Balance']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    # Company info
    ws.cell(row=2, column=1, value=f"Company: {company.name if company else 'N/A'}")
    ws.cell(row=3, column=1, value=f"Account: {account.name}")
    ws.cell(row=4, column=1, value=f"Financial Year: {fy}")
    
    # Transaction data
    running_balance = float(account.opening_dr or 0) - float(account.opening_cr or 0)
    row = 6
    
    for line, header in transactions:
        debit = float(line.debit or 0)
        credit = float(line.credit or 0)
        
        if debit > 0:
            running_balance += debit
        else:
            running_balance -= credit
        
        ws.cell(row=row, column=1, value=header.voucher_date.strftime('%d-%m-%Y'))
        ws.cell(row=row, column=2, value=header.voucher_no)
        ws.cell(row=row, column=3, value=(line.narration or header.narration)[:100])
        ws.cell(row=row, column=4, value=debit if debit > 0 else '')
        ws.cell(row=row, column=5, value=credit if credit > 0 else '')
        ws.cell(row=row, column=6, value=running_balance)
        
        # Format currency columns
        ws.cell(row=row, column=4).number_format = '#,##0.00'
        ws.cell(row=row, column=5).number_format = '#,##0.00'
        ws.cell(row=row, column=6).number_format = '#,##0.00'
        
        row += 1
    
    # Auto-adjust column widths
    for col in range(1, 7):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15
    
    # Save to BytesIO
    buffer = BytesIO()
    wb.save(buffer)
    
    # Return Excel file
    buffer.seek(0)
    excel_data = buffer.getvalue()
    
    filename = f"account_ledger_{account.name}_{fy}.xlsx"
    return Response(
        excel_data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@reports_bp.route("/reports/ledger")
@reports_bp.route("/reports/ledger/<int:party_id>")
@login_required
def ledger(party_id=None):
    """Legacy ledger route - redirects to account ledger"""
    if party_id:
        return redirect(url_for('reports.account_ledger', account_id=party_id))
    else:
        return redirect(url_for('reports.quick_ledger'))

@reports_bp.route("/reports/outstanding")
@login_required
def outstanding():
    """Outstanding balances report"""
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Get all accounts with balances
    start, end = fy_dates(fy)
    
    # Get accounts with outstanding balances
    accounts = Account.query.filter_by(company_id=cid, is_active=True).all()
    
    outstanding_data = []
    
    for account in accounts:
        # Calculate balance for this account
        debits_query = db.session.query(func.sum(JournalLine.debit)).join(JournalHeader).filter(
            JournalLine.account_id == account.id,
            JournalHeader.company_id == cid,
            JournalHeader.voucher_date >= start,
            JournalHeader.voucher_date <= end
        ).scalar() or 0.0
        
        credits_query = db.session.query(func.sum(JournalLine.credit)).join(JournalHeader).filter(
            JournalLine.account_id == account.id,
            JournalHeader.company_id == cid,
            JournalHeader.voucher_date >= start,
            JournalHeader.voucher_date <= end
        ).scalar() or 0.0
        
        opening_balance = float(account.opening_dr or 0) - float(account.opening_cr or 0)
        current_balance = opening_balance + float(debits_query) - float(credits_query)
        
        # Only include accounts with non-zero balances
        if abs(current_balance) > 0.01:
            outstanding_data.append({
                'account_name': account.name,
                'group_name': account.group_name,
                'balance': current_balance,
                'balance_type': 'Dr' if current_balance > 0 else 'Cr'
            })
    
    # Sort by balance amount
    outstanding_data.sort(key=lambda x: abs(x['balance']), reverse=True)
    
    return render_template("reports/outstanding.html",
                         outstanding_data=outstanding_data,
                         fy=fy)

@reports_bp.route("/reports/quick-ledger")
@login_required
def quick_ledger():
    cid = session.get("company_id")
    fy = session.get("fin_year")
    start, end = fy_dates(fy)
    
    # Get all accounts for quick search
    accounts = Account.query.filter_by(company_id=cid, is_active=True).order_by(Account.name).all()
    
    # Pre-compute account balances from journal lines
    account_bal_query = db.session.query(
        JournalLine.account_id,
        func.sum(JournalLine.debit).label("dr"),
        func.sum(JournalLine.credit).label("cr"),
    ).join(JournalHeader, JournalHeader.id == JournalLine.journal_header_id
    ).filter(
        JournalHeader.company_id == cid,
        JournalHeader.voucher_date >= start,
        JournalHeader.voucher_date <= end,
        JournalHeader.is_cancelled == False
    ).group_by(JournalLine.account_id).all()
    
    account_txn_bal = {r.account_id: float(r.dr or 0) - float(r.cr or 0) for r in account_bal_query}
    
    # Get all parties for quick search
    parties = Party.query.filter_by(company_id=cid, is_active=True).order_by(Party.name).all()
    
    # Pre-compute party balances from bills + cash book
    party_bill_totals = {}
    bill_rows = db.session.query(
        Bill.party_id,
        Bill.bill_type,
        func.sum(Bill.total_amount).label("total")
    ).filter(
        Bill.company_id == cid, Bill.fin_year == fy, Bill.is_cancelled == False
    ).group_by(Bill.party_id, Bill.bill_type).all()
    
    for r in bill_rows:
        if r.party_id not in party_bill_totals:
            party_bill_totals[r.party_id] = 0.0
        amt = float(r.total or 0)
        if r.bill_type == 'Purchase':
            party_bill_totals[r.party_id] += amt  # We owe = debit for party
        elif r.bill_type in ('Sales', 'Sale'):
            party_bill_totals[r.party_id] -= amt  # They owe = credit for party
    
    # Combine accounts and parties - skip accounts that duplicate party names
    all_ledgers = []
    party_names_lower = {p.name.lower() for p in parties}
    
    # Add accounts (skip those that are just party duplicates)
    for account in accounts:
        if account.account_type == 'Party' and account.name.lower() in party_names_lower:
            continue  # Skip - party already represents this entity
        
        opening = float(account.opening_dr or 0) - float(account.opening_cr or 0)
        txn_bal = account_txn_bal.get(account.id, 0.0)
        
        # Check if this is a milk-related account
        is_milk = False
        if account.name:
            name_lower = account.name.lower()
            if any(keyword in name_lower for keyword in ['milk', 'purchase', 'sale']):
                is_milk = True
        if account.group_name and 'milk' in account.group_name.lower():
            is_milk = True
        
        all_ledgers.append({
            'id': account.id,
            'name': account.name,
            'type': 'Account',
            'entity': 'account',
            'group_name': account.group_name or '',
            'account_type': account.account_type or '',
            'balance': round(opening + txn_bal, 2),
            'is_milk': is_milk,
            'party_type': None
        })
    
    # Add parties
    for party in parties:
        opening_balance = float(party.opening_balance or 0)
        balance_type = party.balance_type or 'Dr'
        
        # Get transaction totals for this party
        transaction_total = party_bill_totals.get(party.id, 0.0)
        
        # Calculate current balance
        if balance_type == 'Dr':
            current_balance = opening_balance + transaction_total
        else:
            current_balance = -opening_balance + transaction_total
        
        # Check if this is a milk-related party
        is_milk = False
        if party.name:
            name_lower = party.name.lower()
            if any(keyword in name_lower for keyword in ['milk', 'dairy', 'farm']):
                is_milk = True
        
        all_ledgers.append({
            'id': party.id,
            'name': party.name,
            'type': 'Party',
            'entity': 'party',
            'group_name': f"Party - {party.party_type}",
            'account_type': 'Party',
            'balance': round(current_balance, 2),
            'is_milk': is_milk,
            'party_type': party.party_type
        })
    
    # Sort by name
    all_ledgers.sort(key=lambda x: x['name'].lower())
    
    return render_template("reports/quick_ledger.html", accounts=all_ledgers)

@reports_bp.route("/reports/account-ledger/<int:account_id>")
@login_required
def account_ledger(account_id):
    cid = session.get("company_id")
    fy = session.get("fin_year")
    entity = (request.args.get("entity") or "").lower()
    report_type = request.args.get("report_type", "")
    
    print(f"DEBUG: account_ledger called with account_id={account_id}, entity='{entity}', report_type='{report_type}'")
    
    # Always treat as Account ledger - no Party logic
    account = Account.query.filter_by(id=account_id, company_id=cid).first()
    if not account:
        print(f"DEBUG: Account {account_id} not found")
        return "Account not found", 404
    
    # Get company details
    company = Company.query.get(cid)
    
    print(f"DEBUG: Found account: {account.name}, group: {account.group_name}")
    print(f"DEBUG: Found company: {company.name if company else 'N/A'}")
    
    entity_name = account.name
    entity_group = account.group_name or "Default Group"
    entity_type = "Account"
    
    # Get financial year dates
    start, end = fy_dates(fy)
    
    # Get Account transactions from JournalLines ONLY
    transactions = db.session.query(
        JournalLine,
        JournalHeader
    ).join(JournalHeader, JournalHeader.id == JournalLine.journal_header_id
    ).filter(
        JournalLine.account_id == account_id,
        JournalHeader.company_id == cid,
        JournalHeader.voucher_date >= start,
        JournalHeader.voucher_date <= end,
        JournalHeader.is_cancelled == False
    ).order_by(JournalHeader.voucher_date, JournalHeader.id).all()
    
    print(f"DEBUG: Found {len(transactions)} journal transactions for account {account.name}")
    
    # Calculate opening balance for Account
    opening_balance = float(account.opening_dr or 0) - float(account.opening_cr or 0)
    
    # Process Account transactions (JournalLines) - Traditional Ledger Format
    transaction_data = []
    running_balance = opening_balance
    
    # Add opening balance entry
    transaction_data.append({
        'date': start,
        'voucher_no': '',
        'type': 'Opening Balance',
        'narration': f'Opening Balance as of {start.strftime("%d-%m-%Y")}',
        'debit': opening_balance if opening_balance > 0 else 0,
        'credit': 0 if opening_balance > 0 else abs(opening_balance),
        'balance': running_balance,
        'qty_liters': None,
        'fat_percentage': None,
        'snf_percentage': None,
        'rate': None,
        'basic_amount': 0,
        'fat_value': 0,
        'snf_value': 0,
        'total_amount': 0,
        'shift': None,
        'bf_clr': None
    })
    
    for line, header in transactions:
        debit = float(line.debit or 0)
        credit = float(line.credit or 0)
        
        # For ledger display, show the SAME side as journal entry
        # If account was DEBITED in journal, show as DEBIT in ledger
        # If account was CREDITED in journal, show as CREDIT in ledger
        # This shows the actual effect on the account
        
        # Check if this is a milk transaction and get details
        qty_liters = None; fat = None; snf = None; rate = None; shift = None; bf_clr = None
        fat_value = 0.0; snf_value = 0.0
        
        narration = line.narration or header.narration or ''
        if 'milk' in narration.lower():
            # Try to find milk transaction by matching narration pattern
            try:
                # Extract voucher number from narration if it's a milk transaction
                mlk_match = re.search(r'MLK-(\d+)', narration)
                if mlk_match:
                    milk_txn_id = int(mlk_match.group(1))
                    milk_txn = MilkTransaction.query.filter_by(id=milk_txn_id, company_id=cid).first()
                    if milk_txn:
                        qty_liters = float(milk_txn.qty_liters) if milk_txn.qty_liters is not None else None
                        fat = float(milk_txn.fat) if milk_txn.fat is not None else None
                        snf = float(milk_txn.snf) if milk_txn.snf is not None else None
                        rate = float(milk_txn.rate) if milk_txn.rate is not None else None
                        shift = milk_txn.shift
                        bf_clr = f"BF:{fat} / CLR:{milk_txn.clr}" if fat is not None and getattr(milk_txn, 'clr', None) is not None else None
                        
                        # Calculate fat and SNF values
                        if qty_liters and (fat or snf):
                            daily_rate = float(rate or 0)
                            if daily_rate > 0:
                                try:
                                    from modules.milk import compute_component_breakdown
                                    calc = compute_component_breakdown(qty_liters, fat or 0, snf or 0, daily_rate)
                                    fat_value = round(calc["bf_kgs"] * calc["bf_rate"], 2)
                                    snf_value = round(calc["snf_kgs"] * calc["snf_rate"], 2)
                                except Exception:
                                    fat_value = 0.0
                                    snf_value = 0.0
            except Exception:
                pass
        
        # Create entry showing same side as journal entry
        if debit > 0:
            running_balance += debit
            transaction_data.append({
                'date': header.voucher_date,
                'voucher_no': header.voucher_no,
                'type': header.voucher_type or 'Journal',
                'narration': narration,
                'debit': debit,
                'credit': 0,
                'balance': running_balance,
                'qty_liters': qty_liters,
                'fat_percentage': fat,
                'snf_percentage': snf,
                'rate': rate,
                'basic_amount': debit,
                'fat_value': fat_value,
                'snf_value': snf_value,
                'total_amount': debit,
                'shift': shift,
                'bf_clr': bf_clr
            })
        elif credit > 0:
            running_balance -= credit
            transaction_data.append({
                'date': header.voucher_date,
                'voucher_no': header.voucher_no,
                'type': header.voucher_type or 'Journal',
                'narration': narration,
                'debit': 0,
                'credit': credit,
                'balance': running_balance,
                'qty_liters': qty_liters,
                'fat_percentage': fat,
                'snf_percentage': snf,
                'rate': rate,
                'basic_amount': credit,
                'fat_value': fat_value,
                'snf_value': snf_value,
                'total_amount': credit,
                'shift': shift,
                'bf_clr': bf_clr
            })
    
    # Calculate totals
    total_transactions = len(transaction_data)
    total_debits = sum(t['debit'] for t in transaction_data)
    total_credits = sum(t['credit'] for t in transaction_data)
    net_change = total_debits - total_credits
    closing_balance = opening_balance + net_change
    
    return render_template("reports/account_ledger.html",
                         account=account,
                         company=company,
                         party=None,  # No Party logic
                         entity_name=entity_name,
                         entity_group=entity_group,
                         entity_type=entity_type,
                         transactions=transaction_data,
                         fy=fy,
                         opening_balance=opening_balance,
                         closing_balance=closing_balance,
                         net_change=net_change,
                         total_transactions=total_transactions,
                         total_debits=total_debits,
                         total_credits=total_credits)
