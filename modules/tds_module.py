# modules/tds_module.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from flask_login import login_required
from extensions import db
from models import Bill, Party
from datetime import date

tds_bp = Blueprint("tds", __name__)

@tds_bp.route("/tds")
@login_required
def index():
    cid  = session.get("company_id")
    fy   = session.get("fin_year")
    payments = db.session.query(Bill, Party).join(Party, Bill.party_id==Party.id).filter(
        Bill.company_id==cid, Bill.fin_year==fy,
        Bill.bill_type=="Purchase", Bill.is_cancelled==False
    ).order_by(Bill.bill_date.desc()).all()
    return render_template("tds/index.html", payments=payments, fy=fy)

@tds_bp.route("/tds/certificate/<int:bill_id>")
@login_required
def certificate(bill_id):
    cid  = session.get("company_id")
    bill = Bill.query.filter_by(id=bill_id, company_id=cid).first_or_404()
    tds_rate   = 0.01 if bill.total_amount > 50000 else 0
    tds_amount = round(float(bill.total_amount) * tds_rate, 2)
    return render_template("tds/certificate.html", bill=bill,
                           tds_rate=tds_rate, tds_amount=tds_amount)
