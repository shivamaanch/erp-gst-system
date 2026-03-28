# modules/company.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Company, FinancialYear, User, Bill, MilkTransaction, JournalHeader
from werkzeug.security import generate_password_hash
from sqlalchemy import text

company_bp = Blueprint("company", __name__)

@company_bp.route("/company")
@login_required
def index():
    cid = session.get("company_id")
    company = Company.query.get(cid)
    fys = FinancialYear.query.filter_by(company_id=cid).order_by(FinancialYear.year_name.desc()).all()
    active_fy = session.get("fin_year")
    
    # Get all companies accessible to this user
    if current_user.is_super_admin:
        all_companies = Company.query.all()
    else:
        all_companies = current_user.accessible_companies.all()
    
    return render_template("company/index.html", company=company, fys=fys, active_fy=active_fy, all_companies=all_companies)

@company_bp.route("/company/switch/<int:company_id>")
@login_required
def switch_company(company_id):
    # Check if user has access to this company
    if current_user.is_super_admin:
        company = Company.query.get_or_404(company_id)
    else:
        company = current_user.accessible_companies.filter_by(id=company_id).first_or_404()
    
    # Switch to this company
    session["company_id"] = company.id
    
    # Get active financial year for this company
    active_fy = FinancialYear.query.filter_by(company_id=company.id, is_active=True).first()
    if active_fy:
        session["fin_year"] = active_fy.year_name
    else:
        # Get most recent FY
        recent_fy = FinancialYear.query.filter_by(company_id=company.id).order_by(FinancialYear.year_name.desc()).first()
        if recent_fy:
            session["fin_year"] = recent_fy.year_name
    
    flash(f"Switched to {company.name}", "success")
    return redirect(url_for("company.index"))

@company_bp.route("/company/edit", methods=["GET","POST"])
@login_required
def edit():
    cid = session.get("company_id")
    company = Company.query.get_or_404(cid)
    if request.method == "POST":
        company.name    = request.form["name"].strip()
        company.business_type = request.form.get("business_type", "Trading")
        company.gstin   = request.form.get("gstin","").strip().upper() or None
        company.address = request.form.get("address","").strip() or None
        company.phone   = request.form.get("phone","").strip() or None
        company.email   = request.form.get("email","").strip() or None
        company.pan     = request.form.get("pan","").strip().upper() or None
        if hasattr(company, "state_code"):
            company.state_code = request.form.get("state_code","").strip() or None
        db.session.commit()
        flash("Company profile updated!", "success")
        return redirect(url_for("company.index"))
    business_types = ["Trading", "Manufacturing", "Service", "Milk", "Mixed"]
    return render_template("company/edit.html", company=company, business_types=business_types)

@company_bp.route("/company/fy/add", methods=["GET","POST"])
@login_required
def add_fy():
    cid = session.get("company_id")
    if request.method == "POST":
        year_name = request.form["year_name"].strip()
        from datetime import date
        y1 = int(year_name[:4])
        existing = FinancialYear.query.filter_by(company_id=cid, year_name=year_name).first()
        if existing:
            flash(f"FY {year_name} already exists!", "warning")
            return redirect(url_for("company.index"))
        fy = FinancialYear(
            company_id = cid,
            year_name  = year_name,
            start_date = date(y1, 4, 1),
            end_date   = date(y1+1, 3, 31),
            is_active  = False,
            is_closed  = False
        )
        db.session.add(fy)
        db.session.commit()
        flash(f"Financial Year {year_name} added!", "success")
        return redirect(url_for("company.index"))
    # Suggest next FY
    from datetime import date
    cy = date.today().year
    existing = [f.year_name for f in FinancialYear.query.filter_by(company_id=cid).all()]
    suggestions = [f"{y}-{str(y+1)[2:]}" for y in range(cy-1, cy+2) if f"{y}-{str(y+1)[2:]}" not in existing]
    return render_template("company/add_fy.html", suggestions=suggestions)

@company_bp.route("/company/fy/switch/<int:fy_id>")
@login_required
def switch_fy(fy_id):
    cid = session.get("company_id")
    fy  = FinancialYear.query.filter_by(id=fy_id, company_id=cid).first_or_404()
    session["fin_year"] = fy.year_name
    flash(f"Switched to FY {fy.year_name}", "info")
    return redirect(url_for("company.index"))

@company_bp.route("/company/fy/activate/<int:fy_id>", methods=["POST"])
@login_required
def activate_fy(fy_id):
    cid = session.get("company_id")
    FinancialYear.query.filter_by(company_id=cid).update({"is_active": False})
    fy  = FinancialYear.query.filter_by(id=fy_id, company_id=cid).first_or_404()
    fy.is_active = True
    session["fin_year"] = fy.year_name
    db.session.commit()
    flash(f"FY {fy.year_name} set as active!", "success")
    return redirect(url_for("company.index"))

@company_bp.route("/company/add", methods=["GET","POST"])
@login_required
def add():
    if request.method == "POST":
        company = Company(
            name=request.form["name"].strip(),
            business_type=request.form.get("business_type", "Trading"),
            gstin=request.form.get("gstin", "").strip().upper() or None,
            address=request.form.get("address", "").strip() or None,
            phone=request.form.get("phone", "").strip() or None,
            email=request.form.get("email", "").strip() or None,
            pan=request.form.get("pan", "").strip().upper() or None,
            is_active=True
        )
        if hasattr(company, "state_code"):
            company.state_code = request.form.get("state_code", "").strip() or None
        
        db.session.add(company)
        db.session.commit()
        
        # Give current user access to this company
        if not current_user.is_super_admin:
            from models import user_companies
            db.session.execute(text("""
                INSERT INTO user_companies (user_id, company_id, role, is_active)
                VALUES (:user_id, :company_id, 'admin', 1)
            """), {"user_id": current_user.id, "company_id": company.id})
            db.session.commit()
        
        flash(f"Company '{company.name}' added successfully!", "success")
        return redirect(url_for("company.index"))
    
    business_types = ["Trading", "Manufacturing", "Service", "Milk", "Mixed"]
    return render_template("company/form.html", company=None, business_types=business_types)

@company_bp.route("/company/edit/<int:company_id>", methods=["GET","POST"])
@login_required
def edit_company(company_id):
    # Check if user has access to edit this company
    if current_user.is_super_admin:
        company = Company.query.get_or_404(company_id)
    else:
        company = current_user.accessible_companies.filter_by(id=company_id).first_or_404()
    
    if request.method == "POST":
        company.name = request.form["name"].strip()
        company.business_type = request.form.get("business_type", "Trading")
        company.gstin = request.form.get("gstin", "").strip().upper() or None
        company.address = request.form.get("address", "").strip() or None
        company.phone = request.form.get("phone", "").strip() or None
        company.email = request.form.get("email", "").strip() or None
        company.pan = request.form.get("pan", "").strip().upper() or None
        company.is_active = request.form.get("is_active") == "1"
        if hasattr(company, "state_code"):
            company.state_code = request.form.get("state_code", "").strip() or None
        
        db.session.commit()
        flash(f"Company '{company.name}' updated successfully!", "success")
        return redirect(url_for("company.index"))
    
    business_types = ["Trading", "Manufacturing", "Service", "Milk", "Mixed"]
    return render_template("company/form.html", company=company, business_types=business_types)

@company_bp.route("/company/delete/<int:company_id>", methods=["POST"])
@login_required
def delete(company_id):
    # Prevent deleting current company
    if company_id == session.get("company_id"):
        flash("Cannot delete the currently active company!", "danger")
        return redirect(url_for("company.index"))
    
    # Check if user has access to delete this company
    if current_user.is_super_admin:
        company = Company.query.get_or_404(company_id)
    else:
        company = current_user.accessible_companies.filter_by(id=company_id).first_or_404()
    
    try:
        # Check for existing records
        bills_count = Bill.query.filter_by(company_id=company_id).count()
        milk_count = MilkTransaction.query.filter_by(company_id=company_id).count()
        journal_count = JournalHeader.query.filter_by(company_id=company_id).count()
        
        if bills_count > 0 or milk_count > 0 or journal_count > 0:
            # Delete all associated data
            db.session.execute(text("DELETE FROM bills WHERE company_id = :cid"), {"cid": company_id})
            db.session.execute(text("DELETE FROM milk_transactions WHERE company_id = :cid"), {"cid": company_id})
            db.session.execute(text("DELETE FROM journal_headers WHERE company_id = :cid"), {"cid": company_id})
            db.session.execute(text("DELETE FROM financial_years WHERE company_id = :cid"), {"cid": company_id})
            db.session.execute(text("DELETE FROM user_companies WHERE company_id = :cid"), {"cid": company_id})
            
            flash(f"Company '{company.name}' and all its data ({bills_count} bills, {milk_count} milk entries, {journal_count} journal entries) have been deleted!", "warning")
        else:
            # Just delete the company
            db.session.execute(text("DELETE FROM user_companies WHERE company_id = :cid"), {"cid": company_id})
            db.session.delete(company)
            flash(f"Company '{company.name}' deleted successfully!", "success")
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting company: {str(e)}", "danger")
    
    return redirect(url_for("company.index"))
