# modules/smf_module.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from flask_login import login_required
from extensions import db
from models import LoanApplication
from datetime import date

smf_bp = Blueprint("smf", __name__)

@smf_bp.route("/smf")
@login_required
def index():
    cid   = session.get("company_id")
    loans = LoanApplication.query.filter_by(company_id=cid).order_by(LoanApplication.created_date.desc()).all()
    return render_template("smf/index.html", loans=loans)

@smf_bp.route("/smf/apply", methods=["GET","POST"])
@login_required
def apply():
    cid = session.get("company_id")
    fy  = session.get("fin_year")
    if request.method == "POST":
        loan = LoanApplication(
            company_id         = cid,
            applicant_name     = request.form["applicant_name"].strip(),
            business_name      = request.form["business_name"].strip(),
            loan_amount        = float(request.form["loan_amount"]),
            loan_purpose       = request.form["loan_purpose"],
            tenure_months      = int(request.form["tenure_months"]),
            existing_loans     = float(request.form.get("existing_loans") or 0),
            collateral_details = request.form.get("collateral_details","").strip(),
            projected_turnover = float(request.form["projected_turnover"]),
            projected_profit   = float(request.form["projected_profit"]),
            created_date       = date.today()
        )
        db.session.add(loan)
        db.session.commit()
        flash("Loan application submitted!", "success")
        return redirect(url_for("smf.index"))
    return render_template("smf/apply.html", fy=fy)

@smf_bp.route("/smf/view/<int:loan_id>")
@login_required
def view(loan_id):
    cid  = session.get("company_id")
    loan = LoanApplication.query.filter_by(id=loan_id, company_id=cid).first_or_404()
    return render_template("smf/view.html", loan=loan)
