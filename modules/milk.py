from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify
from flask_login import login_required
from extensions import db
from models import MilkRateChart, MilkTransaction, Party, Bill, BillItem
from datetime import date, datetime

milk_bp = Blueprint("milk", __name__)

def calc_rate(fat, snf, fat_rate, snf_rate):
    return round(float(fat)*float(fat_rate) + float(snf)*float(snf_rate), 4)

def next_bill_no(company_id, fin_year, bill_type):
    prefix = "MLK-S" if bill_type == "Sales" else "MLK-P"
    last = Bill.query.filter(Bill.company_id==company_id, Bill.fin_year==fin_year, Bill.bill_no.like(f"{prefix}%")).order_by(Bill.id.desc()).first()
    num = 1
    if last:
        try: num = int(last.bill_no.split("-")[-1]) + 1
        except: num = 1
    return f"{prefix}-{num:04d}"

@milk_bp.route("/milk/rates")
@login_required
def rates():
    cid = session.get("company_id")
    charts = MilkRateChart.query.filter_by(company_id=cid, is_active=True).order_by(MilkRateChart.effective_date.desc()).all()
    return render_template("milk/rates.html", charts=charts)

@milk_bp.route("/milk/rates/add", methods=["GET","POST"])
@login_required
def add_rate():
    cid = session.get("company_id")
    if request.method == "POST":
        rc = MilkRateChart(
            company_id=cid, chart_name=request.form["chart_name"].strip(),
            effective_date=datetime.strptime(request.form["effective_date"],"%Y-%m-%d").date(),
            fat_rate=float(request.form["fat_rate"]), snf_rate=float(request.form["snf_rate"]),
            base_fat=float(request.form.get("base_fat") or 0),
            base_snf=float(request.form.get("base_snf") or 0),
            txn_type=request.form.get("txn_type","Both"), is_active=True)
        db.session.add(rc); db.session.commit()
        flash("Rate chart saved!", "success")
        return redirect(url_for("milk.rates"))
    return render_template("milk/rate_form_traditional.html", chart=None, today=date.today().isoformat())

@milk_bp.route("/milk/rates/edit/<int:cid_>", methods=["GET","POST"])
@login_required
def edit_rate(cid_):
    cid   = session.get("company_id")
    chart = MilkRateChart.query.filter_by(id=cid_, company_id=cid).first_or_404()
    if request.method == "POST":
        chart.chart_name=request.form["chart_name"].strip()
        chart.effective_date=datetime.strptime(request.form["effective_date"],"%Y-%m-%d").date()
        chart.fat_rate=float(request.form["fat_rate"]); chart.snf_rate=float(request.form["snf_rate"])
        chart.base_fat=float(request.form.get("base_fat") or 0)
        chart.base_snf=float(request.form.get("base_snf") or 0)
        chart.txn_type=request.form.get("txn_type","Both")
        db.session.commit(); flash("Updated!", "success")
        return redirect(url_for("milk.rates"))
    return render_template("milk/rate_form_traditional.html", chart=chart, today=date.today().isoformat())

@milk_bp.route("/milk/entry")
@login_required
def entry_list():
    cid  = session.get("company_id"); fy = session.get("fin_year")
    txns = MilkTransaction.query.filter_by(company_id=cid, fin_year=fy).order_by(MilkTransaction.txn_date.desc()).limit(200).all()
    total_qty = sum(float(t.qty_liters) for t in txns)
    total_amt = sum(float(t.amount) for t in txns)
    return render_template("milk/entry_list.html", txns=txns, total_qty=total_qty, total_amt=total_amt)

@milk_bp.route("/milk/entry/add", methods=["GET","POST"])
@login_required
def add_entry():
    cid     = session.get("company_id"); fy = session.get("fin_year")
    parties = Party.query.filter_by(company_id=cid, is_active=True).order_by(Party.name).all()
    charts  = MilkRateChart.query.filter_by(company_id=cid, is_active=True).order_by(MilkRateChart.effective_date.desc()).all()
    if request.method == "POST":
        fat=float(request.form["fat"]); 
        snf=float(request.form.get("snf", request.form.get("snf_auto", 8.5)))
        qty=float(request.form["qty_liters"])
        
        # Handle rate chart selection
        chart_id=request.form.get("chart_id")
        if chart_id and chart_id != "":
            chart=MilkRateChart.query.get(int(chart_id))
            fat_rate=chart.fat_rate; snf_rate=chart.snf_rate
        else:
            fat_rate=float(request.form.get("fat_rate", 200))
            snf_rate=float(request.form.get("snf_rate", 100))
        
        # Calculate using traditional method
        rate=calc_rate(fat,snf,fat_rate,snf_rate)
        amount=round(rate*qty,2)
        
        txn_type=request.form["txn_type"]; party_id=int(request.form["party_id"])
        txn_date=datetime.strptime(request.form["txn_date"],"%Y-%m-%d").date()
        create_invoice=request.form.get("create_invoice")=="1"
        txn=MilkTransaction(company_id=cid,fin_year=fy,party_id=party_id,txn_date=txn_date,
            shift=request.form.get("shift","Morning"),txn_type=txn_type,
            qty_liters=qty,fat=fat,snf=snf,rate=rate,amount=amount,
            chart_id=chart_id,narration=request.form.get("narration","").strip())
        db.session.add(txn)
        bill_no=None
        if create_invoice:
            bill_type="Sales" if txn_type=="Sale" else "Purchase"
            bill_no=next_bill_no(cid,fy,bill_type)
            gst_rate=float(request.form.get("gst_rate") or 0)
            gst_amt=round(amount*gst_rate/100,2); total=round(amount+gst_amt,2)
            bill=Bill(company_id=cid,fin_year=fy,party_id=party_id,bill_no=bill_no,
                bill_date=txn_date,bill_type=bill_type,taxable_amount=amount,
                gst_amount=gst_amt,total_amount=total,
                narration=f"Milk {txn_type} | FAT:{fat}% SNF:{snf}% | {qty}L @ Rs{rate}/L",
                is_cancelled=False)
            db.session.add(bill); db.session.flush()
            item=BillItem(bill_id=bill.id,item_name="Milk",hsn_code="0401",qty=qty,
                unit="Ltr",rate=rate,taxable_amt=amount,gst_rate=gst_rate,
                gst_amt=gst_amt,total_amt=total)
            db.session.add(item); txn.bill_id=bill.id
        db.session.commit()
        msg=f"Saved {qty}L @ Rs{rate}/L = Rs{amount}"
        if bill_no: msg+=f" | Invoice {bill_no} created"
        flash(msg,"success")
        return redirect(url_for("milk.entry_list"))
    return render_template("milk/entry_form_traditional.html", parties=parties, charts=charts, today=date.today().isoformat())

@milk_bp.route("/api/milk-rate")
@login_required
def api_rate():
    cid=session.get("company_id"); chart_id=request.args.get("chart_id")
    fat=float(request.args.get("fat",0)); snf=float(request.args.get("snf",0))
    qty=float(request.args.get("qty",0))
    chart=MilkRateChart.query.filter_by(id=chart_id,company_id=cid).first()
    if not chart: return jsonify({"rate":0,"amount":0})
    rate=calc_rate(fat,snf,chart.fat_rate,chart.snf_rate)
    return jsonify({"rate":rate,"amount":round(rate*qty,2)})

@milk_bp.route("/milk/summary")
@login_required
def summary():
    cid=session.get("company_id"); fy=session.get("fin_year")
    from sqlalchemy import func
    data=db.session.query(MilkTransaction.txn_type,Party.name,
        func.sum(MilkTransaction.qty_liters).label("total_qty"),
        func.sum(MilkTransaction.amount).label("total_amt"),
        func.avg(MilkTransaction.fat).label("avg_fat"),
        func.avg(MilkTransaction.snf).label("avg_snf"),
    ).join(Party,MilkTransaction.party_id==Party.id).filter(
        MilkTransaction.company_id==cid,MilkTransaction.fin_year==fy
    ).group_by(MilkTransaction.txn_type,Party.name).all()
    return render_template("milk/summary.html", data=data, fy=fy)
