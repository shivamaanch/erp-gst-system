from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import FinancialYear, Account, JournalHeader, JournalLine, ComplianceAlert
from datetime import date, datetime

year_bp = Blueprint("year", __name__)

@year_bp.route("/year-closing")
@login_required
def index():
    cid = session.get("company_id")
    years = FinancialYear.query.filter_by(company_id=cid).order_by(FinancialYear.start_date.desc()).all()
    return render_template("year/index.html", years=years)

@year_bp.route("/year-closing/close/<int:fy_id>", methods=["POST"])
@login_required
def close_year(fy_id):
    cid = session.get("company_id")
    fy  = FinancialYear.query.get_or_404(fy_id)
    if fy.is_closed:
        flash("This year is already closed.", "warning")
        return redirect(url_for("year.index"))

    # Get P&L accounts and compute net profit
    accounts = Account.query.filter_by(company_id=cid).all()
    net_profit = 0
    for acc in accounts:
        if acc.account_type in ["Income","Sales"]:
            net_profit += float(acc.opening_cr or 0) - float(acc.opening_dr or 0)
        elif acc.account_type in ["Expense","Purchase"]:
            net_profit -= float(acc.opening_dr or 0) - float(acc.opening_cr or 0)

    # Create closing journal entry
    retained = Account.query.filter_by(company_id=cid, name="Retained Earnings").first()
    if retained and net_profit != 0:
        jh = JournalHeader(
            company_id=cid, fin_year=fy.year_name,
            voucher_no=f"YC-{fy.year_name}",
            voucher_type="Year Closing",
            voucher_date=fy.end_date,
            narration=f"Year closing entry for {fy.year_name}",
            created_by=current_user.id,
        )
        db.session.add(jh); db.session.flush()
        if net_profit > 0:
            db.session.add(JournalLine(journal_header_id=jh.id, account_id=retained.id,
                                        credit=abs(net_profit)))
        else:
            db.session.add(JournalLine(journal_header_id=jh.id, account_id=retained.id,
                                        debit=abs(net_profit)))

    fy.is_closed = True
    fy.is_active = False

    # Create new FY
    new_start = date(fy.end_date.year + 1, 4, 1)
    new_end   = date(fy.end_date.year + 2, 3, 31)
    new_year  = f"{new_start.year}-{str(new_end.year)[2:]}"
    existing_new = FinancialYear.query.filter_by(company_id=cid, year_name=new_year).first()
    if not existing_new:
        new_fy = FinancialYear(company_id=cid, year_name=new_year,
                                start_date=new_start, end_date=new_end, is_active=True)
        db.session.add(new_fy)

    db.session.commit()
    flash(f"✅ Year {fy.year_name} closed. New year {new_year} created.", "success")
    return redirect(url_for("year.index"))
