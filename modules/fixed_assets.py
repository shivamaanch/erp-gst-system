"""
Fixed Assets Schedule Module
Manage fixed assets with depreciation calculation and posting
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import login_required
from extensions import db
from models import Account, JournalHeader, JournalLine
from datetime import datetime, date
from decimal import Decimal

fixed_assets_bp = Blueprint("fixed_assets", __name__)

@fixed_assets_bp.route("/fixed-assets/schedule")
@login_required
def schedule():
    """Fixed Assets Schedule with depreciation"""
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Get all fixed asset accounts (using group_name since Account model doesn't have groups)
    assets = Account.query.filter_by(
        company_id=cid, group_name="Fixed Assets", is_active=True
    ).all()
    
    if not assets:
        flash("No fixed assets found. Please add fixed assets first.", "info")
        # Return empty schedule
        assets = []
    
    # Calculate depreciation for each asset as per Income Tax Act
    asset_schedule = []
    for asset in assets:
        # Get asset details
        opening_wdv = float(asset.opening_dr or 0)  # Written Down Value at start of year
        additions = 0  # New additions during the year
        sales = 0  # Sales/disposals during the year
        
        # Determine depreciation rate based on asset category (as per IT Act)
        depreciation_rate = get_it_act_depreciation_rate(asset.name)
        
        # Calculate depreciation as per IT Act (on WDV basis)
        # For new assets, half rate if purchased after 180 days from year end
        depreciation_base = opening_wdv + additions - sales
        annual_depreciation = depreciation_base * (depreciation_rate / 100)
        closing_wdv = depreciation_base - annual_depreciation
        
        asset_schedule.append({
            'id': asset.id,
            'name': asset.name,
            'category': get_asset_category(asset.name),
            'opening_wdv': opening_wdv,
            'additions': additions,
            'sales': sales,
            'depreciation_rate': depreciation_rate,
            'annual_depreciation': annual_depreciation,
            'closing_wdv': closing_wdv
        })
    
    total_opening_wdv = sum(a['opening_wdv'] for a in asset_schedule)
    total_additions = sum(a['additions'] for a in asset_schedule)
    total_sales = sum(a['sales'] for a in asset_schedule)
    total_depreciation = sum(a['annual_depreciation'] for a in asset_schedule)
    total_closing_wdv = sum(a['closing_wdv'] for a in asset_schedule)
    
    return render_template("fixed_assets/schedule_it_act.html",
                         assets=asset_schedule,
                         total_opening_wdv=total_opening_wdv,
                         total_additions=total_additions,
                         total_sales=total_sales,
                         total_depreciation=total_depreciation,
                         total_closing_wdv=total_closing_wdv,
                         fy=fy)

def get_it_act_depreciation_rate(asset_name):
    """Get depreciation rate as per Income Tax Act based on asset name"""
    asset_name_lower = asset_name.lower()
    
    # Building and Civil Works - 10%
    if any(word in asset_name_lower for word in ['building', 'construction', 'civil', 'structure']):
        return 10.0
    
    # Plant & Machinery - 15%
    if any(word in asset_name_lower for word in ['plant', 'machinery', 'equipment', 'machine']):
        return 15.0
    
    # Motor Cars - 15%
    if any(word in asset_name_lower for word in ['car', 'vehicle', 'auto', 'motor']):
        return 15.0
    
    # Furniture & Fittings - 10%
    if any(word in asset_name_lower for word in ['furniture', 'fixture', 'fitting', 'chair', 'table']):
        return 10.0
    
    # Computers & Software - 40%
    if any(word in asset_name_lower for word in ['computer', 'laptop', 'software', 'server', 'printer']):
        return 40.0
    
    # Intangible Assets - 25%
    if any(word in asset_name_lower for word in ['patent', 'copyright', 'trademark', 'goodwill']):
        return 25.0
    
    # Default rate for other assets - 15%
    return 15.0

def get_asset_category(asset_name):
    """Get asset category as per Income Tax Act"""
    asset_name_lower = asset_name.lower()
    
    if any(word in asset_name_lower for word in ['building', 'construction', 'civil', 'structure']):
        return "Building"
    elif any(word in asset_name_lower for word in ['plant', 'machinery', 'equipment', 'machine']):
        return "Plant & Machinery"
    elif any(word in asset_name_lower for word in ['car', 'vehicle', 'auto', 'motor']):
        return "Motor Vehicle"
    elif any(word in asset_name_lower for word in ['furniture', 'fixture', 'fitting', 'chair', 'table']):
        return "Furniture & Fittings"
    elif any(word in asset_name_lower for word in ['computer', 'laptop', 'software', 'server', 'printer']):
        return "Computer & Software"
    elif any(word in asset_name_lower for word in ['patent', 'copyright', 'trademark', 'goodwill']):
        return "Intangible Asset"
    else:
        return "Other Assets"

@fixed_assets_bp.route("/fixed-assets/post-depreciation", methods=["POST"])
@login_required
def post_depreciation():
    """Post depreciation journal entry"""
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    try:
        # Get depreciation account
        depreciation_acc = Account.query.filter_by(
            company_id=cid, name="Depreciation", is_active=True
        ).first()
        
        if not depreciation_acc:
            return jsonify({"success": False, "message": "Depreciation account not found"})
        
        # Get total depreciation from form
        total_depreciation = float(request.form.get("total_depreciation", 0))
        
        if total_depreciation <= 0:
            return jsonify({"success": False, "message": "No depreciation to post"})
        
        # Create journal entry
        from utils.voucher_helper import generate_voucher_number
        voucher_no = generate_voucher_number(cid, fy, 'Journal')
        
        journal = JournalHeader(
            company_id=cid,
            fin_year=fy,
            voucher_no=voucher_no,
            voucher_type="Journal",
            voucher_date=date.today(),
            narration=f"Depreciation for FY {fy}",
            created_by=session.get("user_id", 1)
        )
        db.session.add(journal)
        db.session.flush()
        
        # Debit: Depreciation Expense
        db.session.add(JournalLine(
            journal_header_id=journal.id,
            account_id=depreciation_acc.id,
            debit=Decimal(total_depreciation),
            credit=0,
            narration="Depreciation charged"
        ))
        
        # Credit: Accumulated Depreciation (or individual assets)
        # For simplicity, credit to Depreciation account itself
        db.session.add(JournalLine(
            journal_header_id=journal.id,
            account_id=depreciation_acc.id,
            debit=0,
            credit=Decimal(total_depreciation),
            narration="Accumulated depreciation"
        ))
        
        db.session.commit()
        
        flash(f"✅ Depreciation posted successfully! Voucher: {voucher_no}", "success")
        return jsonify({"success": True, "voucher_no": voucher_no})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})

@fixed_assets_bp.route("/fixed-assets/add", methods=["GET", "POST"])
@login_required
def add_asset():
    """Add new fixed asset"""
    cid = session.get("company_id")
    
    if request.method == "POST":
        try:
            # Create new asset account (using group_name)
            asset = Account(
                company_id=cid,
                name=request.form.get("asset_name"),
                group_name="Fixed Assets",
                account_type="Asset",
                is_active=True,
                opening_dr=float(request.form.get("opening_value", 0)),
                opening_cr=0
            )
            db.session.add(asset)
            db.session.commit()
            
            flash(f"✅ Fixed asset '{asset.name}' added successfully!", "success")
            return redirect(url_for('fixed_assets.schedule'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error adding asset: {str(e)}", "error")
    
    return render_template("fixed_assets/add.html")
