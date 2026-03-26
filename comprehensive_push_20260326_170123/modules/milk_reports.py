# modules/milk_reports.py
from flask import Blueprint, render_template, request, session
from flask_login import login_required
from extensions import db
from models import Bill, Party, Company
from sqlalchemy import func, extract, and_, or_
from datetime import date, datetime
from utils.filters import get_month_options, get_period_from_request, parse_period

milk_reports_bp = Blueprint("milk_reports", __name__)

@milk_reports_bp.route("/milk-reports/statement")
@login_required
def milk_statement():
    cid = session.get("company_id")
    fy = session.get("fin_year")
    period = get_period_from_request()
    farmer_name = request.args.get("farmer_name", "")
    
    # Parse period
    start_date, end_date = parse_period(period)
    
    # Get milk collection data
    query = db.session.query(
        Bill, Party
    ).join(Party, Bill.party_id == Party.id).filter(
        Bill.company_id == cid,
        Bill.fin_year == fy,
        Bill.bill_type == "Sales",  # Milk collection recorded as sales
        Bill.bill_date >= start_date,
        Bill.bill_date <= end_date,
        Bill.template_type == "Milk",
        Bill.is_cancelled == False
    )
    
    # Filter by farmer name if provided
    if farmer_name:
        query = query.filter(Party.name.ilike(f"%{farmer_name}%"))
    
    bills_data = query.order_by(Bill.bill_date.desc()).all()
    
    # Calculate totals and averages
    total_quantity = 0
    total_basic_amount = 0
    total_fat_value = 0
    total_snf_value = 0
    total_amount = 0
    total_deductions = 0
    collection_days = 0
    
    # Process bills data
    milk_entries = []
    for bill, party in bills_data:
        # Parse bill items (assuming milk data stored in narration or items)
        items = []
        try:
            # Try to parse items from bill (this would need to be implemented based on your data structure)
            # For now, we'll use the bill totals as demonstration
            quantity = float(bill.taxable_amount or 0) / 50  # Example calculation
            fat_percentage = 3.5  # Example - should come from actual data
            snf_percentage = 8.5   # Example - should come from actual data
            rate_per_liter = float(bill.total_amount or 0) / quantity if quantity > 0 else 0
            
            basic_amount = quantity * rate_per_liter
            fat_value = basic_amount * (fat_percentage / 100) * 0.5  # Example rate
            snf_value = basic_amount * (snf_percentage / 100) * 0.3  # Example rate
            total_amount = basic_amount + fat_value + snf_value
            
            items.append({
                'date': bill.bill_date,
                'quantity': quantity,
                'fat_percentage': fat_percentage,
                'snf_percentage': snf_percentage,
                'rate_per_liter': rate_per_liter,
                'basic_amount': basic_amount,
                'fat_value': fat_value,
                'snf_value': snf_value,
                'total_amount': total_amount
            })
            
            total_quantity += quantity
            total_basic_amount += basic_amount
            total_fat_value += fat_value
            total_snf_value += snf_value
            total_amount += total_amount
            collection_days += 1
            
        except Exception as e:
            # Skip if parsing fails
            continue
        
        milk_entries.append({
            'bill': bill,
            'party': party,
            'items': items,
            'total_amount': total_amount
        })
    
    # Calculate averages
    average_fat = 0
    average_snf = 0
    average_daily = 0
    
    if collection_days > 0:
        average_fat = 3.5  # Would calculate from actual data
        average_snf = 8.5  # Would calculate from actual data
        average_daily = total_amount / collection_days
    
    # Get unique farmers for dropdown
    farmers = db.session.query(Party).join(Bill, Party.id == Bill.party_id).filter(
        Bill.company_id == cid,
        Bill.template_type == "Milk",
        Bill.is_cancelled == False
    ).distinct().order_by(Party.name).all()
    
    return render_template("milk_reports/statement.html",
                         milk_entries=milk_entries,
                         farmers=farmers,
                         total_quantity=total_quantity,
                         total_basic_amount=total_basic_amount,
                         total_fat_value=total_fat_value,
                         total_snf_value=total_snf_value,
                         total_amount=total_amount,
                         total_deductions=total_deductions,
                         average_fat=average_fat,
                         average_snf=average_snf,
                         average_daily=average_daily,
                         collection_days=collection_days,
                         start_date=start_date,
                         end_date=end_date,
                         farmer_name=farmer_name,
                         month_options=get_month_options())

@milk_reports_bp.route("/milk-reports/farmer-summary")
@login_required
def farmer_summary():
    cid = session.get("company_id")
    fy = session.get("fin_year")
    period = get_period_from_request()
    
    # Parse period
    start_date, end_date = parse_period(period)
    
    # Get farmer-wise summary
    farmer_summary = db.session.query(
        Party.name,
        func.count(Bill.id).label('collection_days'),
        func.sum(Bill.total_amount).label('total_amount'),
        func.avg(Bill.total_amount).label('average_daily')
    ).join(Bill, Party.id == Bill.party_id).filter(
        Bill.company_id == cid,
        Bill.fin_year == fy,
        Bill.bill_type == "Sales",
        Bill.bill_date >= start_date,
        Bill.bill_date <= end_date,
        Bill.template_type == "Milk",
        Bill.is_cancelled == False
    ).group_by(Party.name).order_by(Party.name).all()
    
    return render_template("milk_reports/farmer_summary.html",
                         farmer_summary=farmer_summary,
                         start_date=start_date,
                         end_date=end_date,
                         month_options=get_month_options())

@milk_reports_bp.route("/milk-reports/quality-report")
@login_required
def quality_report():
    cid = session.get("company_id")
    fy = session.get("fin_year")
    period = get_period_from_request()
    
    # Parse period
    start_date, end_date = parse_period(period)
    
    # Get quality statistics
    quality_data = db.session.query(
        func.count(Bill.id).label('samples'),
        func.avg(Bill.taxable_amount).label('avg_quantity'),
        func.sum(Bill.total_amount).label('total_amount')
    ).filter(
        Bill.company_id == cid,
        Bill.fin_year == fy,
        Bill.bill_type == "Sales",
        Bill.bill_date >= start_date,
        Bill.bill_date <= end_date,
        Bill.template_type == "Milk",
        Bill.is_cancelled == False
    ).first()
    
    # Daily quality trends
    daily_data = db.session.query(
        Bill.bill_date,
        func.count(Bill.id).label('collections'),
        func.sum(Bill.total_amount).label('total_amount')
    ).filter(
        Bill.company_id == cid,
        Bill.fin_year == fy,
        Bill.bill_type == "Sales",
        Bill.bill_date >= start_date,
        Bill.bill_date <= end_date,
        Bill.template_type == "Milk",
        Bill.is_cancelled == False
    ).group_by(Bill.bill_date).order_by(Bill.bill_date).all()
    
    return render_template("milk_reports/quality_report.html",
                         quality_data=quality_data,
                         daily_data=daily_data,
                         start_date=start_date,
                         end_date=end_date,
                         month_options=get_month_options())
