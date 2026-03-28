# modules/accounts.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify
from flask_login import login_required
from extensions import db
from models import Account
from modules.permissions import require_role
from datetime import date

accounts_bp = Blueprint("accounts", __name__)

ACCOUNT_GROUPS = [
    "Assets", "Fixed Assets", "Current Assets", "Bank", "Cash",
    "Liabilities", "Capital Account", "Reserves & Surplus", "Secured Loans", "Unsecured Loans",
    "Current Liabilities", "Sundry Creditors", "Duties & Taxes",
    "Income", "Sales", "Direct Income", "Indirect Income", "Other Income",
    "Expenses", "Purchase", "Direct Expense", "Indirect Expense", "Depreciation",
    "Sundry Debtors", "Loans & Advances", "Stock in Hand", "Cost of Goods Sold"
]

@accounts_bp.route("/accounts")
@login_required
def index():
    cid = session.get("company_id")
    group_filter = request.args.get("group", "")
    search = request.args.get("q", "")
    
    # Debug output
    print(f"DEBUG: Company ID from session: {cid}")
    print(f"DEBUG: Group filter: '{group_filter}'")
    print(f"DEBUG: Search: '{search}'")
    
    query = Account.query.filter_by(company_id=cid, is_active=True)
    if group_filter:
        query = query.filter_by(group_name=group_filter)
    if search:
        query = query.filter(Account.name.ilike(f"%{search}%"))
    
    accounts = query.order_by(Account.group_name, Account.name).all()
    
    print(f"DEBUG: Found {len(accounts)} accounts")
    
    # Group accounts by group_name
    grouped = {}
    for acc in accounts:
        grp = acc.group_name or "Uncategorized"
        if grp not in grouped:
            grouped[grp] = []
        grouped[grp].append(acc)
    
    print(f"DEBUG: Grouped into {len(grouped)} groups")
    
    return render_template("accounts/index.html", 
                         grouped_accounts=grouped, 
                         account_groups=ACCOUNT_GROUPS,
                         group_filter=group_filter,
                         search=search)

@accounts_bp.route("/accounts/add", methods=["GET", "POST"])
@login_required
def add():
    cid = session.get("company_id")
    if request.method == "POST":
        account = Account(
            company_id=cid,
            name=request.form["name"].strip(),
            group_name=request.form.get("group_name"),
            account_type=request.form.get("account_type", "General"),
            opening_dr=float(request.form.get("opening_dr", 0)),
            opening_cr=float(request.form.get("opening_cr", 0)),
            is_active=True
        )
        db.session.add(account)
        db.session.commit()
        flash(f"Account '{account.name}' added successfully!", "success")
        return redirect(url_for("accounts.index"))
    return render_template("accounts/form.html", account=None, groups=ACCOUNT_GROUPS, title="Add Account")

@accounts_bp.route("/accounts/edit/<int:acc_id>", methods=["GET", "POST"])
@login_required
def edit(acc_id):
    cid = session.get("company_id")
    account = Account.query.filter_by(id=acc_id, company_id=cid).first_or_404()
    if request.method == "POST":
        account.name = request.form["name"].strip()
        account.group_name = request.form.get("group_name")
        account.account_type = request.form.get("account_type", "General")
        account.opening_dr = float(request.form.get("opening_dr", 0))
        account.opening_cr = float(request.form.get("opening_cr", 0))
        db.session.commit()
        flash(f"Account '{account.name}' updated!", "success")
        return redirect(url_for("accounts.index"))
    return render_template("accounts/form.html", account=account, groups=ACCOUNT_GROUPS, title="Edit Account")

@accounts_bp.route("/accounts/delete/<int:acc_id>", methods=["POST"])
@login_required
def delete(acc_id):
    cid = session.get("company_id")
    account = Account.query.filter_by(id=acc_id, company_id=cid).first_or_404()
    account.is_active = False
    db.session.commit()
    flash(f"Account '{account.name}' deactivated.", "warning")
    return redirect(url_for("accounts.index"))

@accounts_bp.route("/accounts/groups")
@login_required
def groups():
    """Show account groups with statistics"""
    cid = session.get("company_id")
    
    # Get all accounts grouped by group_name
    accounts = Account.query.filter_by(company_id=cid, is_active=True).all()
    
    # Group statistics
    group_stats = {}
    for acc in accounts:
        grp = acc.group_name or "Uncategorized"
        if grp not in group_stats:
            group_stats[grp] = {
                'count': 0,
                'total_dr': 0,
                'total_cr': 0,
                'accounts': []
            }
        group_stats[grp]['count'] += 1
        group_stats[grp]['total_dr'] += float(acc.opening_dr or 0)
        group_stats[grp]['total_cr'] += float(acc.opening_cr or 0)
        group_stats[grp]['accounts'].append(acc)
    
    return render_template("accounts/groups.html", 
                         group_stats=group_stats,
                         total_accounts=len(accounts))

@accounts_bp.route("/accounts/quick-add", methods=["POST"])
@login_required
def quick_add():
    cid = session.get("company_id")
    
    try:
        # Create new account
        account = Account(
            company_id=cid,
            name=request.form["name"].strip(),
            account_type=request.form["account_type"],
            opening_balance=float(request.form.get("opening_balance", 0)),
            balance_type=request.form.get("balance_type", "debit"),
            description=request.form.get("description", "").strip(),
            is_active=True,
            created_at=date.today()
        )
        
        # Set opening balance based on type
        if account.balance_type == "debit":
            account.opening_dr = account.opening_balance
            account.opening_cr = 0
        else:
            account.opening_dr = 0
            account.opening_cr = account.opening_balance
        
        db.session.add(account)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Account added successfully"})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})
