# modules/alerts_module.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from flask_login import login_required
from extensions import db
from models import Party, Bill
from datetime import date

alerts_bp = Blueprint("alerts", __name__)

@alerts_bp.route("/alerts")
@login_required
def index():
    cid   = session.get("company_id")
    fy    = session.get("fin_year")
    today = date.today()
    alerts = []

    # GSTR-1 due on 10th of next month
    if today.month == 12:
        gstr1_due = date(today.year+1, 1, 10)
    else:
        gstr1_due = date(today.year, today.month+1, 10)
    days = (gstr1_due - today).days
    if days <= 7:
        alerts.append({"type":"warning","icon":"bi-file-earmark-text",
                       "title":"GSTR-1 Due Soon",
                       "message":f"File GSTR-1 by {gstr1_due.strftime('%d-%b-%Y')} ({days} days left)",
                       "url":"/gstr1"})

    # TDS due on 7th of next month
    if today.month == 12:
        tds_due = date(today.year+1, 1, 7)
    else:
        tds_due = date(today.year, today.month+1, 7)
    days_tds = (tds_due - today).days
    if days_tds <= 5:
        alerts.append({"type":"danger","icon":"bi-percent",
                       "title":"TDS Payment Due",
                       "message":f"Pay TDS by {tds_due.strftime('%d-%b-%Y')} ({days_tds} days left)",
                       "url":"/tds"})

    # Parties without GSTIN/PAN
    unverified = Party.query.filter_by(company_id=cid, is_active=True).filter(
        (Party.gstin==None)|(Party.gstin=="")).count()
    if unverified:
        alerts.append({"type":"warning","icon":"bi-exclamation-triangle",
                       "title":"Incomplete Party Records",
                       "message":f"{unverified} party(ies) missing GSTIN",
                       "url":"/clients"})

    return render_template("alerts/index.html", alerts=alerts)
