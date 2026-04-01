# modules/reports_module.py
from flask import Blueprint, render_template, request, session
from flask_login import login_required
from extensions import db
from models import Party, Bill, Company, Account, JournalLine, JournalHeader
from sqlalchemy import func
from datetime import date

reports_bp = Blueprint("reports", __name__)

def get_account_balances():
    """Get individual account balances for Balance Sheet"""
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Get financial year dates
    from utils.filters import fy_dates
    start, end = fy_dates(fy)
    
    # Get all account balances
    account_balances = db.session.query(
        Account.id,
        Account.name,
        Account.group_name,
        func.sum(JournalLine.debit).label("dr"),
        func.sum(JournalLine.credit).label("cr"),
    ).join(JournalLine, JournalLine.account_id == Account.id
    ).join(JournalHeader, JournalHeader.id == JournalLine.journal_header_id
    ).filter(
        Account.company_id == cid,
        JournalHeader.company_id == cid,
        JournalHeader.voucher_date <= end,
        JournalHeader.is_cancelled == False,
        Account.is_active == True
    ).group_by(Account.id, Account.name, Account.group_name).all()
    
    # Calculate balances and filter non-zero balances
    balances = {}
    for acc in account_balances:
        balance = float(acc.dr or 0) - float(acc.cr or 0)
        if abs(balance) > 0.01:  # Only include accounts with balance
            balances[acc.id] = {
                'name': acc.name,
                'group': acc.group_name,
                'balance': balance
            }
    return balances

@reports_bp.route("/reports/hub")
@login_required
def hub():
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Get sales and purchase data
    total_sales     = float(db.session.query(func.sum(Bill.total_amount)).filter_by(
        company_id=cid, fin_year=fy, bill_type="Sales", is_cancelled=False).scalar() or 0)
    total_purchases = float(db.session.query(func.sum(Bill.total_amount)).filter_by(
        company_id=cid, fin_year=fy, bill_type="Purchase", is_cancelled=False).scalar() or 0)
    sales_count     = Bill.query.filter_by(company_id=cid, fin_year=fy, bill_type="Sales", is_cancelled=False).count()
    purchase_count  = Bill.query.filter_by(company_id=cid, fin_year=fy, bill_type="Purchase", is_cancelled=False).count()
    
    # Calculate actual financial position from database
    from utils.filters import fy_dates
    start, end = fy_dates(fy)
    
    # Get all account balances for financial position
    account_balances = db.session.query(
        Account.id,
        Account.name,
        Account.group_name,
        func.sum(JournalLine.debit).label("dr"),
        func.sum(JournalLine.credit).label("cr"),
    ).join(JournalLine, JournalLine.account_id == Account.id
    ).join(JournalHeader, JournalHeader.id == JournalLine.journal_header_id
    ).filter(
        Account.company_id == cid,
        JournalHeader.company_id == cid,
        JournalHeader.voucher_date <= end,
        JournalHeader.is_cancelled == False,
        Account.is_active == True
    ).group_by(Account.id, Account.name, Account.group_name).all()
    
    # Calculate financial position
    financial_position = 0.0
    for acc in account_balances:
        balance = float(acc.dr or 0) - float(acc.cr or 0)
        
        # Add opening balance if available
        if hasattr(acc, 'opening_dr') and acc.opening_dr:
            balance += float(acc.opening_dr)
        if hasattr(acc, 'opening_cr') and acc.opening_cr:
            balance -= float(acc.opening_cr)
        
        financial_position += balance
    
    # Calculate net profit
    net_profit = total_sales - total_purchases
    
    return render_template("reports/hub.html", fy=fy,
                           total_sales=total_sales, total_purchases=total_purchases,
                           sales_count=sales_count, purchase_count=purchase_count,
                           net_profit=net_profit,
                           financial_position=financial_position,
                           current_date=date.today())

@reports_bp.route("/reports/quick-ledger")
@login_required
def quick_ledger():
    cid = session.get("company_id")
    
    # Get all accounts for quick search
    accounts = Account.query.filter_by(company_id=cid, is_active=True).order_by(Account.name).all()
    
    # Get all parties for quick search (milk entry parties)
    from models import Party
    parties = Party.query.filter_by(company_id=cid, is_active=True).order_by(Party.name).all()
    
    # Combine accounts and parties for comprehensive ledger search
    all_ledgers = []
    
    # Add accounts
    for account in accounts:
        all_ledgers.append({
            'id': account.id,
            'name': account.name,
            'type': 'Account',
            'entity': 'account',
            'group_name': account.group_name,
            'account_type': account.account_type,
            'balance': float(account.opening_dr or 0) - float(account.opening_cr or 0)
        })
    
    # Add parties
    for party in parties:
        all_ledgers.append({
            'id': party.id,
            'name': party.name,
            'type': 'Party',
            'entity': 'party',
            'party_type': party.party_type,
            'gstin': party.gstin,
            'phone': party.phone,
            'balance': float(party.opening_balance or 0) * (1 if party.balance_type == 'Dr' else -1)
        })
    
    # Sort by name
    all_ledgers.sort(key=lambda x: x['name'])
    
    return render_template("reports/quick_ledger.html", accounts=all_ledgers)

@reports_bp.route("/reports/account-ledger/<int:account_id>")
@login_required
def account_ledger(account_id):
    from utils.filters import fy_dates
    from models import MilkTransaction
    
    cid = session.get("company_id")
    fy = session.get("fin_year")
    entity = (request.args.get("entity") or "").lower()
    
    # Resolve entity explicitly to avoid account/party id collisions
    account = None
    party = None

    from models import Party
    if entity == "party":
        party = Party.query.filter_by(id=account_id, company_id=cid).first()
    elif entity == "account":
        account = Account.query.filter_by(id=account_id, company_id=cid).first()
    else:
        account = Account.query.filter_by(id=account_id, company_id=cid).first()
        if not account:
            party = Party.query.filter_by(id=account_id, company_id=cid).first()
    
    # Determine entity details
    if account:
        entity_name = account.name
        entity_group = account.group_name or "Default Group"
        entity_type = "Account"
    elif party:
        entity_name = party.name
        entity_group = f"Party - {party.party_type}"
        entity_type = "Party"
    else:
        entity_name = "Unknown Entity"
        entity_group = "Default Group"
        entity_type = "Unknown"
    
    # Get financial year dates
    start, end = fy_dates(fy)
    
    # Get transactions for this entity
    transactions = []
    
    if account:
        # Get Account transactions from JournalLines
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
    
    elif party:
        # Get Party transactions from Bills (milk entries, invoices, etc.)
        from models import Bill
        transactions = Bill.query.filter(
            Bill.party_id == party.id,
            Bill.company_id == cid,
            Bill.fin_year == fy,
            Bill.is_cancelled == False
        ).order_by(Bill.bill_date, Bill.id).all()
    
    # Calculate opening balance
    opening_balance = 0.0
    if account:
        opening_balance = float(account.opening_dr or 0) - float(account.opening_cr or 0)
    elif party:
        opening_balance = float(party.opening_balance or 0) * (1 if party.balance_type == 'Dr' else -1)
    
    # Calculate running balance
    running_balance = opening_balance
    transaction_data = []
    
    if account:
        # Process Account transactions (JournalLines)
        for line, header in transactions:
            debit = float(line.debit or 0)
            credit = float(line.credit or 0)
            
            if debit > 0:
                running_balance += debit
            else:
                running_balance -= credit
            
            transaction_data.append({
                'date': header.voucher_date,
                'voucher_no': header.voucher_no,
                'type': header.voucher_type or 'Journal',
                'narration': line.narration or header.narration or '',
                'debit': debit,
                'credit': credit,
                'balance': running_balance
            })
    
    elif party:
        # Process Party transactions (Bills)
        for bill in transactions:
            amount = float(bill.total_amount or 0)
            narration = bill.narration or f'{bill.bill_type} - {bill.bill_no}'
            
            # Try to get milk transaction details (may not exist for all bills)
            qty_liters = None
            fat = None
            snf = None
            rate = None
            shift = None
            bf_clr = None
            
            try:
                milk_txn = MilkTransaction.query.filter_by(company_id=cid, bill_id=bill.id).order_by(MilkTransaction.id.desc()).first()
                if milk_txn:
                    qty_liters = float(milk_txn.qty_liters) if milk_txn.qty_liters is not None else None
                    fat = float(milk_txn.fat) if milk_txn.fat is not None else None
                    snf = float(milk_txn.snf) if milk_txn.snf is not None else None
                    rate = float(milk_txn.rate) if milk_txn.rate is not None else None
                    shift = milk_txn.shift
                    bf_clr = f"BF:{fat} / CLR:{milk_txn.clr}" if fat is not None and getattr(milk_txn, 'clr', None) is not None else None
            except Exception as e:
                # If milk transaction lookup fails, continue without milk details
                print(f"Warning: Could not fetch milk transaction for bill {bill.id}: {e}")
            
            basic_amount = amount
            fat_value = 0.0
            snf_value = 0.0
            
            # Determine debit/credit based on bill type and party type
            # Purchase bills = we owe them (credit/payable)
            # Sale bills = they owe us (debit/receivable)
            if bill.bill_type == 'Purchase':
                # We purchased from them - credit (we owe)
                debit = 0
                credit = amount
                running_balance -= amount
            elif bill.bill_type in ['Sale', 'Sales']:
                # We sold to them - debit (they owe)
                debit = amount
                credit = 0
                running_balance += amount
            else:
                # Default behavior
                debit = amount
                credit = 0
                running_balance += amount
            
            transaction_data.append({
                'date': bill.bill_date,
                'voucher_no': bill.bill_no,
                'type': bill.bill_type or 'Bill',
                'voucher_type': bill.bill_type or 'Bill',
                'narration': narration,
                'debit': debit,
                'credit': credit,
                'balance': running_balance,
                'qty_liters': qty_liters,
                'fat_percentage': fat,
                'snf_percentage': snf,
                'rate': rate,
                'basic_amount': basic_amount,
                'fat_value': fat_value,
                'snf_value': snf_value,
                'total_amount': amount,
                'shift': shift,
                'bf_clr': bf_clr
            })
    
    # Calculate totals
    total_debits = sum(t['debit'] for t in transaction_data)
    total_credits = sum(t['credit'] for t in transaction_data)
    closing_balance = running_balance
    net_change = closing_balance - opening_balance
    total_transactions = len(transaction_data)
    
    return render_template("reports/account_ledger.html",
                         account=account,
                         party=party,
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

@reports_bp.route("/reports/account-ledger/<int:account_id>/pdf")
@login_required
def account_ledger_pdf(account_id):
    from utils.filters import fy_dates
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from io import BytesIO
    from flask import Response
    
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Get account details (handle default accounts)
    account = Account.query.get(account_id) if account_id > 0 else None
    account_name = account.name if account else "Default Account"
    
    # Get financial year dates
    start, end = fy_dates(fy)
    
    # Get transactions (only if real account exists)
    transactions = []
    if account:
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
        ).order_by(JournalHeader.voucher_date, JournalLine.id).all()
    
    # Create PDF
    doc = SimpleDocTemplate("buffer", pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Add custom ParagraphStyle
    styles.add(ParagraphStyle('CustomTitle', fontSize=16, textColor=colors.black, alignment=1))
    
    story = []
    
    # Company header
    story.append(Paragraph("Account Ledger", styles['CustomTitle']))
    story.append(Spacer(1, 12))
    
    # Account info
    story.append(Paragraph(f"Account: {account_name}", styles['Normal']))
    story.append(Paragraph(f"Financial Year: {fy}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Table data
    data = [['Date', 'Voucher No', 'Type', 'Narration', 'Debit', 'Credit', 'Balance']]
    
    running_balance = 0.0
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
            header.voucher_type or 'Journal',
            line.narration or header.narration or '',
            f"₹{debit:.2f}" if debit > 0 else '',
            f"₹{credit:.2f}" if credit > 0 else '',
            f"₹{running_balance:.2f}"
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(table)
    doc.build(story)
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    response = Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={account_name}_Ledger.pdf'}
    )
    return response

@reports_bp.route("/reports/account-ledger/<int:account_id>/excel")
@login_required
def account_ledger_excel(account_id):
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from io import BytesIO
    from flask import Response
    
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Get account details (handle default accounts)
    account = Account.query.get(account_id) if account_id > 0 else None
    account_name = account.name if account else "Default Account"
    
    # Get financial year dates
    start, end = fy_dates(fy)
    
    # Get transactions (only if real account exists)
    transactions = []
    if account:
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
        ).order_by(JournalHeader.voucher_date, JournalLine.id).all()
    
    # Create Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"{account_name} Ledger"
    
    # Headers
    headers = ['Date', 'Voucher No', 'Type', 'Narration', 'Debit', 'Credit', 'Balance']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="1F4E79")
        cell.alignment = Alignment(horizontal="center")
    
    # Data
    running_balance = 0.0
    for i, (line, header) in enumerate(transactions, 2):
        debit = float(line.debit or 0)
        credit = float(line.credit or 0)
        
        if debit > 0:
            running_balance += debit
        else:
            running_balance -= credit
        
        ws.cell(row=i, column=1, value=header.voucher_date.strftime('%d-%m-%Y'))
        ws.cell(row=i, column=2, value=header.voucher_no)
        ws.cell(row=i, column=3, value=header.voucher_type or 'Journal')
        ws.cell(row=i, column=4, value=line.narration or header.narration or '')
        ws.cell(row=i, column=5, value=debit if debit > 0 else '')
        ws.cell(row=i, column=6, value=credit if credit > 0 else '')
        ws.cell(row=i, column=7, value=running_balance)
    
    # Format currency columns
    for row in range(2, len(transactions) + 2):
        for col in [5, 6, 7]:  # Debit, Credit, Balance columns
            cell = ws.cell(row=row, column=col)
            if cell.value:
                cell.number_format = '₹#,##0.00'
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    response = Response(
        buffer.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename={account_name}_Ledger.xlsx'}
    )
    return response

@reports_bp.route("/reports/profit_loss")
@login_required
def profit_loss():
    cid  = session.get("company_id")
    fy   = session.get("fin_year")
    
    # Get company
    company = Company.query.get(cid)
    
    # Calculate sales and purchases
    sales_total = float(db.session.query(func.sum(Bill.total_amount)).filter_by(
        company_id=cid, fin_year=fy, bill_type="Sales", is_cancelled=False).scalar() or 0)
    purchase_total = float(db.session.query(func.sum(Bill.total_amount)).filter_by(
        company_id=cid, fin_year=fy, bill_type="Purchase", is_cancelled=False).scalar() or 0)
    
    # Calculate profits
    gross_profit = sales_total - purchase_total
    net_profit = gross_profit  # Simplified - no indirect expenses yet
    total_expenses = purchase_total
    total_income = sales_total
    
    # Use horizontal template by default
    return render_template("reports/profit_loss_horizontal.html", 
                           fy=fy,
                           company=company,
                           sales=sales_total,
                           purchases=purchase_total,
                           gross_profit=gross_profit,
                           net_profit=net_profit,
                           total_expenses=total_expenses,
                           total_income=total_income,
                           fiscal_year_end=f"31 Mar {int(fy[:4])+1}",
                           current_date=date.today())

@reports_bp.route("/reports/balance_sheet")
@login_required
def balance_sheet():
    cid  = session.get("company_id")
    fy   = session.get("fin_year")
    
    # Get company
    company = Company.query.get(cid)
    
    # Get account balances for detailed display
    account_balances = get_account_balances()
    
    # Get Fixed Assets data from Fixed Assets Schedule
    from modules.fixed_assets import get_fixed_assets_schedule
    fixed_assets_schedule = get_fixed_assets_schedule(cid, fy)
    
    # Calculate simplified totals (keeping existing logic for compatibility)
    creditors = Party.query.filter_by(company_id=cid, party_type="Creditor", is_active=True).all()
    debtors   = Party.query.filter_by(company_id=cid, party_type="Debtor", is_active=True).all()
    creditors = sum(float(c.opening_balance or 0) for c in creditors if (c.balance_type or "Cr") == "Cr")
    debtors   = sum(float(d.opening_balance or 0) for d in debtors if (d.balance_type or "Dr") == "Dr")
    
    # Capital and reserves (simplified)
    share_capital_acc = Account.query.filter_by(company_id=cid, name="Share Capital", is_active=True).first()
    capital = float(share_capital_acc.opening_dr or 0) if share_capital_acc else 0
    
    reserves_acc = Account.query.filter_by(company_id=cid, name="General Reserve", is_active=True).first()
    retained = float(reserves_acc.opening_dr or 0) if reserves_acc else 0
    
    # Calculate total fixed assets from schedule
    total_fixed_assets = fixed_assets_schedule['total_closing_wdv'] if fixed_assets_schedule else 0.0
    
    total_liabilities = capital + retained + creditors
    total_assets      = debtors + total_fixed_assets + (total_liabilities - debtors - total_fixed_assets)  # balance
    
    # Use horizontal template by default
    return render_template("reports/balance_sheet_horizontal.html", 
                           fy=fy,
                           company=company,
                           debtors=debtors, 
                           creditors=creditors,
                           retained_earnings=retained, 
                           capital=capital,
                           total_liabilities=total_liabilities, 
                           total_assets=total_assets,
                           account_balances=account_balances,
                           fixed_assets_schedule=fixed_assets_schedule,
                           fiscal_year_end=f"31 Mar {int(fy[:4])+1}",
                           current_date=date.today())

@reports_bp.route("/reports/trial_balance")
@login_required
def trial_balance():
    cid  = session.get("company_id")
    fy   = session.get("fin_year")
    parties = Party.query.filter_by(company_id=cid, is_active=True).all()
    tb_data = []
    total_debit = total_credit = 0
    for p in parties:
        bal = float(p.opening_balance or 0)
        if bal == 0: continue
        if (p.balance_type or "Dr") == "Dr":
            tb_data.append({"account": p.name, "debit": bal, "credit": 0})
            total_debit += bal
        else:
            tb_data.append({"account": p.name, "debit": 0, "credit": bal})
            total_credit += bal
    return render_template("reports/trial_balance.html", fy=fy,
                           tb_data=tb_data, total_debit=total_debit, total_credit=total_credit,
                           fiscal_year_end=f"31 Mar {int(fy[:4])+1}",
                           current_date=date.today())

@reports_bp.route("/reports/ledger")
@reports_bp.route("/reports/ledger/<int:party_id>")
@login_required
def ledger(party_id=None):
    cid     = session.get("company_id")
    fy      = session.get("fin_year")
    parties = Party.query.filter_by(company_id=cid, is_active=True).order_by(Party.name).all()
    if party_id is None and parties:
        party_id = parties[0].id
    party   = Party.query.filter_by(id=party_id, company_id=cid).first() if party_id else None
    ledger_entries = []
    if party:
        bills    = Bill.query.filter_by(company_id=cid, party_id=party_id, fin_year=fy,
                                        is_cancelled=False).order_by(Bill.bill_date).all()
        running  = float(party.opening_balance or 0) if (party.balance_type or "Dr")=="Dr"                    else -float(party.opening_balance or 0)
        for b in bills:
            amt = float(b.total_amount)
            if b.bill_type == "Sales":
                running += amt
                ledger_entries.append({"date": b.bill_date, "particulars": f"Sales Invoice {b.bill_no}",
                                       "debit": amt, "credit": 0, "balance": running})
            else:
                running -= amt
                ledger_entries.append({"date": b.bill_date, "particulars": f"Purchase Bill {b.bill_no}",
                                       "debit": 0, "credit": amt, "balance": running})
    return render_template("reports/ledger.html", party=party, parties=parties,
                           fy=fy, ledger_entries=ledger_entries)

@reports_bp.route("/reports/outstanding")
@login_required
def outstanding():
    cid     = session.get("company_id")
    fy      = session.get("fin_year")
    debtors = Party.query.filter_by(company_id=cid, party_type="Debtor", is_active=True).all()
    creditors = Party.query.filter_by(company_id=cid, party_type="Creditor", is_active=True).all()
    return render_template("reports/outstanding.html", fy=fy, debtors=debtors, creditors=creditors)

@reports_bp.route("/reports/balance_sheet/pdf")
@login_required
def balance_sheet_pdf():
    """Download Balance Sheet as PDF"""
    from flask import flash, redirect, url_for
    flash("PDF download feature coming soon!", "info")
    return redirect(url_for('reports.balance_sheet'))

@reports_bp.route("/reports/balance_sheet/excel")
@login_required
def balance_sheet_excel():
    """Download Balance Sheet as Excel"""
    from flask import flash, redirect, url_for
    flash("Excel download feature coming soon!", "info")
    return redirect(url_for('reports.balance_sheet'))

@reports_bp.route("/reports/profit_loss/pdf")
@login_required
def profit_loss_pdf():
    """Download P&L as PDF"""
    from flask import flash, redirect, url_for
    flash("PDF download feature coming soon!", "info")
    return redirect(url_for('reports.profit_loss'))

@reports_bp.route("/reports/profit_loss/excel")
@login_required
def profit_loss_excel():
    """Download P&L as Excel"""
    from flask import flash, redirect, url_for
    flash("Excel download feature coming soon!", "info")
    return redirect(url_for('reports.profit_loss'))
