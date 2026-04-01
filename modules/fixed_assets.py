"""
Fixed Assets Schedule Module
Manage fixed assets with custom depreciation calculation and posting
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import login_required
from extensions import db
from models import Account, JournalHeader, JournalLine, FixedAsset, DepreciationBlock
from datetime import datetime, date
from decimal import Decimal

fixed_assets_bp = Blueprint("fixed_assets", __name__)

def get_fixed_assets_schedule(company_id, fin_year):
    """Get fixed assets schedule data for Balance Sheet"""
    # Get all fixed assets for the company (temporarily removing fin_year filter due to schema issue)
    assets = FixedAsset.query.filter_by(
        company_id=company_id, is_active=True
    ).all()
    
    if not assets:
        return {
            'assets': [],
            'total_opening_wdv': 0.0,
            'total_additions': 0.0,
            'total_sales': 0.0,
            'total_depreciation': 0.0,
            'total_closing_wdv': 0.0
        }
    
    # Calculate depreciation for each asset
    asset_schedule = []
    for asset in assets:
        # Calculate depreciation
        asset.calculate_depreciation()
        db.session.commit()
        
        asset_schedule.append({
            'id': asset.id,
            'name': asset.asset_name,
            'category': asset.asset_category,
            'depreciation_block': asset.depreciation_block,
            'depreciation_rate': asset.depreciation_rate,
            'opening_wdv': asset.opening_wdv,
            'additions': asset.additions,
            'sales': asset.sales,
            'annual_depreciation': asset.annual_depreciation,
            'closing_wdv': asset.closing_wdv
        })
    
    total_opening_wdv = sum(a['opening_wdv'] for a in asset_schedule)
    total_additions = sum(a['additions'] for a in asset_schedule)
    total_sales = sum(a['sales'] for a in asset_schedule)
    total_depreciation = sum(a['annual_depreciation'] for a in asset_schedule)
    total_closing_wdv = sum(a['closing_wdv'] for a in asset_schedule)
    
    return {
        'assets': asset_schedule,
        'total_opening_wdv': total_opening_wdv,
        'total_additions': total_additions,
        'total_sales': total_sales,
        'total_depreciation': total_depreciation,
        'total_closing_wdv': total_closing_wdv
    }

@fixed_assets_bp.route("/fixed-assets/schedule")
@login_required
def schedule():
    """Fixed Assets Schedule with depreciation"""
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Get fixed assets from database (temporarily removing fin_year filter due to schema issue)
    assets = FixedAsset.query.filter_by(
        company_id=cid, is_active=True
    ).all()
    
    # Get depreciation blocks
    depreciation_blocks = DepreciationBlock.query.filter_by(
        company_id=cid, is_active=True
    ).all()
    
    # Calculate depreciation for each asset
    for asset in assets:
        asset.calculate_depreciation()
    
    total_opening_wdv = sum(asset.opening_wdv for asset in assets)
    total_additions = sum(asset.additions for asset in assets)
    total_sales = sum(asset.sales for asset in assets)
    total_depreciation = sum(asset.annual_depreciation for asset in assets)
    total_closing_wdv = sum(asset.closing_wdv for asset in assets)
    
    return render_template("fixed_assets/schedule_it_act.html",
                         assets=assets,
                         depreciation_blocks=depreciation_blocks,
                         total_opening_wdv=total_opening_wdv,
                         total_additions=total_additions,
                         total_sales=total_sales,
                         total_depreciation=total_depreciation,
                         total_closing_wdv=total_closing_wdv,
                         fy=fy)

@fixed_assets_bp.route("/fixed-assets/add", methods=["GET", "POST"])
@login_required
def add_asset():
    """Add new fixed asset"""
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    if request.method == "POST":
        try:
            asset = FixedAsset(
                company_id=cid,
                # fin_year=fy,  # Temporarily commented out due to schema issue
                asset_name=request.form.get("asset_name"),
                asset_category=request.form.get("asset_category"),
                description=request.form.get("description"),
                opening_wdv=float(request.form.get("opening_wdv", 0)),
                purchase_date=datetime.strptime(request.form.get("purchase_date"), "%Y-%m-%d").date() if request.form.get("purchase_date") else None,
                purchase_cost=float(request.form.get("purchase_cost", 0)),
                depreciation_method=request.form.get("depreciation_method", "WDV"),
                depreciation_rate=float(request.form.get("depreciation_rate", 15.0)),
                depreciation_block=request.form.get("depreciation_block", "General"),
                is_active=True
            )
            
            # Calculate depreciation
            asset.calculate_depreciation()
            
            db.session.add(asset)
            db.session.commit()
            
            flash("Fixed asset added successfully!", "success")
            return redirect(url_for("fixed_assets.schedule"))
            
        except Exception as e:
            flash(f"Error adding asset: {str(e)}", "error")
            return redirect(url_for("fixed_assets.add"))
    
    # Get depreciation blocks for dropdown
    depreciation_blocks = DepreciationBlock.query.filter_by(company_id=cid, is_active=True).all()
    
    return render_template("fixed_assets/add_asset.html",
                         depreciation_blocks=depreciation_blocks,
                         fy=fy)

@fixed_assets_bp.route("/fixed-assets/edit/<int:asset_id>", methods=["GET", "POST"])
@login_required
def edit_asset(asset_id):
    """Edit existing fixed asset"""
    cid = session.get("company_id")
    
    asset = FixedAsset.query.get_or_404(asset_id)
    
    if asset.company_id != cid:
        flash("Access denied!", "error")
        return redirect(url_for("fixed_assets.schedule"))
    
    if request.method == "POST":
        try:
            asset.asset_name = request.form.get("asset_name")
            asset.asset_category = request.form.get("asset_category")
            asset.description = request.form.get("description")
            asset.opening_wdv = float(request.form.get("opening_wdv", 0))
            asset.purchase_cost = float(request.form.get("purchase_cost", 0))
            asset.depreciation_method = request.form.get("depreciation_method", "WDV")
            asset.depreciation_rate = float(request.form.get("depreciation_rate", 15.0))
            asset.depreciation_block = request.form.get("depreciation_block", "General")
            
            # Recalculate depreciation
            asset.calculate_depreciation()
            
            db.session.commit()
            
            flash("Fixed asset updated successfully!", "success")
            return redirect(url_for("fixed_assets.schedule"))
            
        except Exception as e:
            flash(f"Error updating asset: {str(e)}", "error")
            return redirect(url_for("fixed_assets.edit", asset_id=asset_id))
    
    # Get depreciation blocks for dropdown
    depreciation_blocks = DepreciationBlock.query.filter_by(company_id=cid, is_active=True).all()
    
    return render_template("fixed_assets/edit_asset.html",
                         asset=asset,
                         depreciation_blocks=depreciation_blocks)

@fixed_assets_bp.route("/fixed-assets/delete/<int:asset_id>", methods=["POST"])
@login_required
def delete_asset(asset_id):
    """Delete fixed asset"""
    cid = session.get("company_id")
    
    asset = FixedAsset.query.get_or_404(asset_id)
    
    if asset.company_id != cid:
        flash("Access denied!", "error")
        return redirect(url_for("fixed_assets.schedule"))
    
    try:
        asset.is_active = False
        db.session.commit()
        flash("Fixed asset deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting asset: {str(e)}", "error")
    
    return redirect(url_for("fixed_assets.schedule"))

@fixed_assets_bp.route("/depreciation-blocks", methods=["GET", "POST"])
@login_required
def depreciation_blocks():
    """Manage depreciation blocks"""
    cid = session.get("company_id")
    
    if request.method == "POST":
        try:
            block = DepreciationBlock(
                company_id=cid,
                block_name=request.form.get("block_name"),
                description=request.form.get("description"),
                default_rate=float(request.form.get("default_rate", 15.0)),
                it_act_rate=float(request.form.get("it_act_rate")) if request.form.get("it_act_rate") else None,
                is_active=True
            )
            
            db.session.add(block)
            db.session.commit()
            
            flash("Depreciation block added successfully!", "success")
            return redirect(url_for("fixed_assets.depreciation_blocks"))
            
        except Exception as e:
            flash(f"Error adding block: {str(e)}", "error")
            return redirect(url_for("fixed_assets.depreciation_blocks"))
    
    blocks = DepreciationBlock.query.filter_by(company_id=cid, is_active=True).all()
    
    return render_template("fixed_assets/depreciation_blocks.html", blocks=blocks)

@fixed_assets_bp.route("/depreciation-blocks/edit/<int:block_id>", methods=["GET", "POST"])
@login_required
def edit_depreciation_block(block_id):
    """Edit depreciation block"""
    cid = session.get("company_id")
    
    block = DepreciationBlock.query.get_or_404(block_id)
    
    if block.company_id != cid:
        flash("Access denied!", "error")
        return redirect(url_for("fixed_assets.depreciation_blocks"))
    
    if request.method == "POST":
        try:
            block.block_name = request.form.get("block_name")
            block.description = request.form.get("description")
            block.default_rate = float(request.form.get("default_rate", 15.0))
            block.it_act_rate = float(request.form.get("it_act_rate")) if request.form.get("it_act_rate") else None
            
            db.session.commit()
            
            flash("Depreciation block updated successfully!", "success")
            return redirect(url_for("fixed_assets.depreciation_blocks"))
            
        except Exception as e:
            flash(f"Error updating block: {str(e)}", "error")
            return redirect(url_for("fixed_assets.edit_depreciation_block", block_id=block_id))
    
    return render_template("fixed_assets/edit_depreciation_block.html", block=block)

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
