# modules/gst_module.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from flask_login import login_required
from extensions import db
from models import Company, Party, Bill
from datetime import date

gst_bp = Blueprint("gst", __name__)

def get_fy_dates(fy_str):
    year = int(fy_str[:4])
    return date(year, 4, 1), date(year+1, 3, 31)

@gst_bp.route("/gstr1")
@login_required
def gstr1():
    cid  = session.get("company_id")
    fy   = session.get("fin_year")
    start, end = get_fy_dates(fy)
    sales = Bill.query.filter_by(company_id=cid, fin_year=fy, bill_type="Sales", is_cancelled=False).all()
    b2b, b2cl, b2cs, exp = [], [], [], []
    for bill in sales:
        party  = bill.party
        gstin  = (party.gstin or "") if party else ""
        is_reg = len(gstin) == 15
        row = {"ctin": gstin, "inv": bill.bill_no,
               "idt": bill.bill_date.strftime("%Y-%m-%d"),
               "val": round(bill.total_amount, 2),
               "pos": getattr(bill, "place_of_supply", "03") or "03",
               "net": round(bill.total_amount, 2)}
        if getattr(bill, "place_of_supply", "") == "9999":
            exp.append(row)
        elif is_reg:
            b2b.append(row)
        elif bill.total_amount > 250000:
            b2cl.append(row)
        else:
            b2cs.append(row)
    return render_template("gst/gstr1.html", fy=fy,
                           period=f"{start.strftime('%b %Y')} - {end.strftime('%b %Y')}",
                           b2b=b2b, b2cl=b2cl, b2cs=b2cs, exp=exp,
                           total_sales=len(sales))

@gst_bp.route("/gstr3b")
@login_required
def gstr3b():
    cid  = session.get("company_id")
    fy   = session.get("fin_year")
    start, end = get_fy_dates(fy)
    from sqlalchemy import func
    total_sales     = db.session.query(func.sum(Bill.total_amount)).filter_by(
        company_id=cid, fin_year=fy, bill_type="Sales", is_cancelled=False).scalar() or 0
    total_purchases = db.session.query(func.sum(Bill.total_amount)).filter_by(
        company_id=cid, fin_year=fy, bill_type="Purchase", is_cancelled=False).scalar() or 0
    tax_on_sales     = round(float(total_sales) * 0.18, 2)
    tax_on_purchases = round(float(total_purchases) * 0.18, 2)
    return render_template("gst/gstr3b.html", fy=fy,
                           period=f"{start.strftime('%b %Y')} - {end.strftime('%b %Y')}",
                           total_sales=total_sales, total_purchases=total_purchases,
                           tax_on_sales=tax_on_sales, tax_on_purchases=tax_on_purchases,
                           net_tax=tax_on_sales - tax_on_purchases)
