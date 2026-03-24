# modules/accounts.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify
from flask_login import login_required
from extensions import db
from models import Account
from modules.permissions import require_role

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
@require_role("Admin", "Manager", "Accountant")
def index():
    cid = session.get("company_id")
    group_filter = request.args.get("group", "")
    search = request.args.get("q", "")
    
    query = Account.query.filter_by(company_id=cid, is_active=True)
    if group_filter:
        query = query.filter_by(group_name=group_filter)
    if search:
        query = query.filter(Account.name.ilike(f"%{search}%"))
    
    accounts = query.order_by(Account.group_name, Account.name).all()
    
    # Group accounts by group_name
    grouped = {}
    for acc in accounts:
        grp = acc.group_name or "Uncategorized"
        if grp not in grouped:
            grouped[grp] = []
        grouped[grp].append(acc)
    
    return render_template("accounts/index.html", 
                         grouped_accounts=grouped, 
                         account_groups=ACCOUNT_GROUPS,
                         group_filter=group_filter,
                         search=search)

@accounts_bp.route("/accounts/add", methods=["GET", "POST"])
@login_required
@require_role("Admin", "Accountant")
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
@require_role("Admin", "Accountant")
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
@require_role("Admin")
def delete(acc_id):
    cid = session.get("company_id")
    account = Account.query.filter_by(id=acc_id, company_id=cid).first_or_404()
    account.is_active = False
    db.session.commit()
    flash(f"Account '{account.name}' deactivated.", "warning")
    return redirect(url_for("accounts.index"))
