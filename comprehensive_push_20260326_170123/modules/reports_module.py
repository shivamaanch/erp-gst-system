# modules/reports_module.py
from flask import Blueprint, render_template, request, session
from flask_login import login_required
from extensions import db
from models import Party, Bill, Company
from sqlalchemy import func
from datetime import date

reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/reports/hub")
@login_required
def hub():
    cid = session.get("company_id")
    fy  = session.get("fin_year")
    total_sales     = float(db.session.query(func.sum(Bill.total_amount)).filter_by(
        company_id=cid, fin_year=fy, bill_type="Sales", is_cancelled=False).scalar() or 0)
    total_purchases = float(db.session.query(func.sum(Bill.total_amount)).filter_by(
        company_id=cid, fin_year=fy, bill_type="Purchase", is_cancelled=False).scalar() or 0)
    sales_count     = Bill.query.filter_by(company_id=cid, fin_year=fy, bill_type="Sales", is_cancelled=False).count()
    purchase_count  = Bill.query.filter_by(company_id=cid, fin_year=fy, bill_type="Purchase", is_cancelled=False).count()
    return render_template("reports/hub.html", fy=fy,
                           total_sales=total_sales, total_purchases=total_purchases,
                           sales_count=sales_count, purchase_count=purchase_count,
                           net_profit=total_sales - total_purchases,
                           current_date=date.today())

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
    
    # Calculate balances
    debtors   = float(db.session.query(func.sum(Party.opening_balance)).filter_by(
        company_id=cid, balance_type="Dr"
    ).scalar() or 0)
    creditors = float(db.session.query(func.sum(Party.opening_balance)).filter_by(
        company_id=cid, balance_type="Cr"
    ).scalar() or 0)
    
    # Get Share Capital and Reserves from accounts (default to 0)
    from models import Account
    share_capital_acc = Account.query.filter_by(company_id=cid, name="Share Capital", is_active=True).first()
    capital = float(share_capital_acc.opening_dr or 0) if share_capital_acc else 0
    
    reserves_acc = Account.query.filter_by(company_id=cid, name="General Reserve", is_active=True).first()
    retained = float(reserves_acc.opening_dr or 0) if reserves_acc else 0
    
    total_liabilities = capital + retained + creditors
    total_assets      = debtors + 50000 + (total_liabilities - debtors - 50000)  # balance
    
    # Use horizontal template by default
    return render_template("reports/balance_sheet_horizontal.html", 
                           fy=fy,
                           company=company,
                           debtors=debtors, 
                           creditors=creditors,
                           retained_earnings=retained, 
                           capital=capital,
                           total_liabilities=total_liabilities, 
                           total_assets=total_liabilities,
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
