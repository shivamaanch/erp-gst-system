from flask import Blueprint, render_template, request, session, jsonify
from flask_login import login_required
from extensions import db
from sqlalchemy import func
from models import Account, Party, JournalHeader, JournalLine, MilkTransaction, Bill, CashBook, Company
from utils.filters import fy_dates
import re

reports_bp = Blueprint("reports", __name__)

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
    
    print(f"DEBUG: Found account: {account.name}, group: {account.group_name}")
    
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
    
    # Calculate running balance
    running_balance = opening_balance
    transaction_data = []
    
    # Process Account transactions (JournalLines)
    for line, header in transactions:
        debit = float(line.debit or 0)
        credit = float(line.credit or 0)
        
        if debit > 0:
            running_balance += debit
        else:
            running_balance -= credit
        
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
        
        transaction_data.append({
            'date': header.voucher_date,
            'voucher_no': header.voucher_no,
            'type': header.voucher_type or 'Journal',
            'narration': narration,
            'debit': debit,
            'credit': credit,
            'balance': running_balance,
            'qty_liters': qty_liters,
            'fat_percentage': fat,
            'snf_percentage': snf,
            'rate': rate,
            'basic_amount': debit + credit,
            'fat_value': fat_value,
            'snf_value': snf_value,
            'total_amount': debit + credit,
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
