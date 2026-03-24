# modules/year_module.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from flask_login import login_required
from extensions import db
from models import FinancialYear, Bill
from datetime import date

year_bp = Blueprint("year", __name__)

@year_bp.route("/year")
@login_required
def index():
    cid  = session.get("company_id")
    fys  = FinancialYear.query.filter_by(company_id=cid).order_by(FinancialYear.year_name.desc()).all()
    return render_template("year/index.html", fys=fys, current_fy=session.get("fin_year"))

@year_bp.route("/year/close/<int:fy_id>", methods=["POST"])
@login_required
def close_fy(fy_id):
    cid = session.get("company_id")
    fy  = FinancialYear.query.filter_by(id=fy_id, company_id=cid).first_or_404()
    if fy.is_closed:
        flash("FY already closed!", "warning")
    else:
        fy.is_closed = True
        db.session.commit()
        flash(f"FY {fy.year_name} closed!", "success")
    return redirect(url_for("year.index"))

@year_bp.route("/year/reopen/<int:fy_id>", methods=["POST"])
@login_required
def open_fy(fy_id):
    cid = session.get("company_id")
    fy  = FinancialYear.query.filter_by(id=fy_id, company_id=cid).first_or_404()
    fy.is_closed = False
    db.session.commit()
    flash(f"FY {fy.year_name} reopened!", "info")
    return redirect(url_for("year.index"))
