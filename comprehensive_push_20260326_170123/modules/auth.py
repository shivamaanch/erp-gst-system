from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Company, FinancialYear, UserCompany, CompanyAccessLog
import bcrypt
from datetime import datetime

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").encode()
        user = User.query.filter_by(username=username, is_active=True).first()
        if user and bcrypt.checkpw(password, user.password_hash.encode()):
            login_user(user)
            
            # For multi-company users, select first accessible company
            if user.is_super_admin:
                # Super admin can access all companies, select first one
                company = Company.query.first()
                user_company = UserCompany.query.filter_by(
                    user_id=user.id, 
                    company_id=company.id, 
                    is_active=True
                ).first()
                role = user_company.role if user_company else 'admin'
            else:
                # Regular user, select first accessible company
                user_company = UserCompany.query.filter_by(
                    user_id=user.id, 
                    is_active=True
                ).first()
                if user_company:
                    company = user_company.company
                    role = user_company.role
                else:
                    flash("No company access assigned. Please contact administrator.", "danger")
                    return render_template("auth/login.html")
            
            fy = FinancialYear.query.filter_by(company_id=company.id, is_active=True).first()
            
            # Update session
            session["company_id"] = company.id
            session["company_name"] = company.name
            session["fin_year"] = fy.year_name if fy else "2025-26"
            session["user_role"] = role
            
            # Log access
            from models import CompanyAccessLog
            access_log = CompanyAccessLog(
                user_id=user.id,
                company_id=company.id,
                action='login',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            db.session.add(access_log)
            db.session.commit()
            
            flash(f"Welcome to {company.name}!", "success")
            return redirect(url_for("reports.hub"))
        flash("Invalid username or password", "danger")
    return render_template("auth/login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    # Log logout
    from models import CompanyAccessLog
    access_log = CompanyAccessLog(
        user_id=current_user.id,
        company_id=session.get('company_id'),
        action='logout',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    db.session.add(access_log)
    db.session.commit()
    
    logout_user()
    session.clear()
    return redirect(url_for("auth.login"))

@auth_bp.route("/switch-company/<int:company_id>")
@login_required
def switch_company(company_id):
    user = current_user
    
    # Check if user has access to this company
    if not user.is_super_admin:
        user_company = UserCompany.query.filter_by(
            user_id=user.id, 
            company_id=company_id, 
            is_active=True
        ).first()
        if not user_company:
            flash("You don't have access to this company!", "danger")
            return redirect(url_for("reports.hub"))
    
    company = Company.query.get_or_404(company_id)
    fy = FinancialYear.query.filter_by(company_id=company_id, is_active=True).first()
    
    # Update session
    old_company_id = session.get("company_id")
    session["company_id"] = company_id
    session["company_name"] = company.name
    session["fin_year"] = fy.year_name if fy else "2025-26"
    session["user_role"] = user_company.role if not user.is_super_admin else 'admin'
    
    # Log company switch
    access_log = CompanyAccessLog(
        user_id=user.id,
        company_id=company_id,
        action='switch',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    db.session.add(access_log)
    db.session.commit()
    
    flash(f"Switched to {company.name}", "success")
    return redirect(url_for("reports.hub"))

@auth_bp.route("/switch-financial-year/<string:fin_year>")
@login_required
def switch_financial_year(fin_year):
    user = current_user
    company_id = session.get("company_id")
    
    if not company_id:
        flash("Please select a company first!", "warning")
        return redirect(url_for("reports.hub"))
    
    # Check if financial year exists for this company
    fy = FinancialYear.query.filter_by(company_id=company_id, year_name=fin_year).first()
    if not fy:
        flash(f"Financial year {fin_year} not found!", "danger")
        return redirect(url_for("reports.hub"))
    
    # Update session
    old_fin_year = session.get("fin_year")
    session["fin_year"] = fin_year
    
    flash(f"Switched to Financial Year: {fin_year}", "success")
    return redirect(url_for("reports.hub"))

from extensions import login_manager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route("/dev-login")
def dev_login():
    """ONE-CLICK login for development — remove in production"""
    from models import User
    user = User.query.filter_by(username="admin", is_active=True).first()
    if user:
        login_user(user)
        session["company_id"] = user.company_id
        from models import FinancialYear
        fy = FinancialYear.query.filter_by(company_id=user.company_id, is_active=True).first()
        if fy:
            session["fin_year"] = fy.year_name
        return redirect(url_for("reports.hub"))
    return redirect(url_for("auth.login"))
