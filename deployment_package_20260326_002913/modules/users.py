# modules/users.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import User, Company, UserCompany
from werkzeug.security import generate_password_hash

users_bp = Blueprint("users", __name__)
ROLES = ["admin", "accountant", "viewer"]
ROLE_DESCRIPTIONS = {
    "admin": "Full system access with all permissions",
    "accountant": "Financial management and reporting access",
    "viewer": "View-only access to reports and data"
}

@users_bp.route("/users")
@login_required
def index():
    cid   = session.get("company_id")
    
    # For super admin, show all users across all companies
    if current_user.is_super_admin:
        users = User.query.order_by(User.username).all()
        # Add company info for each user
        user_data = []
        for user in users:
            user_companies = UserCompany.query.filter_by(user_id=user.id, is_active=True).all()
            company_names = [uc.company.name for uc in user_companies]
            user_data.append({
                'user': user,
                'companies': user_companies,
                'company_names': company_names
            })
        return render_template("users/index_multi.html", user_data=user_data, roles=ROLES, role_desc=ROLE_DESCRIPTIONS)
    else:
        # Regular user - show only users for current company
        users = User.query.filter_by(company_id=cid).order_by(User.username).all()
        return render_template("users/index.html", users=users, roles=ROLES, role_desc=ROLE_DESCRIPTIONS)

@users_bp.route("/users/add", methods=["GET","POST"])
@login_required
def add():
    cid = session.get("company_id")
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        email    = request.form.get("email","").strip() or None
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash(f"Username '{username}' already exists!", "danger")
            return render_template("users/form.html", user=None, roles=ROLES, title="Add User")
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_active=True
        )
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Add user to current company
        if not current_user.is_super_admin:
            # Regular user - add to current company
            user_company = UserCompany(
                user_id=user.id,
                company_id=cid,
                role=request.form.get("role","viewer")
            )
            db.session.add(user_company)
        else:
            # Super admin - add to selected companies
            selected_companies = request.form.getlist("companies")
            for company_id in selected_companies:
                user_company = UserCompany(
                    user_id=user.id,
                    company_id=company_id,
                    role=request.form.get(f"role_{company_id}", "viewer")
                )
                db.session.add(user_company)
        
        db.session.commit()
        flash("User created successfully!", "success")
        return redirect(url_for("users.index"))
    
    # Get available companies for assignment
    if current_user.is_super_admin:
        companies = Company.query.all()
    else:
        companies = [current_user.current_company]
    
    return render_template("users/form.html", user=None, companies=companies, roles=ROLES, title="Add User")

@users_bp.route("/users/companies/<int:uid>")
@login_required
def companies(uid):
    user = User.query.get_or_404(uid)
    user_companies = UserCompany.query.filter_by(user_id=uid, is_active=True).all()
    all_companies = Company.query.all()
    
    return render_template("users/companies.html", user=user, user_companies=user_companies, all_companies=all_companies)

@users_bp.route("/users/companies/<int:uid>", methods=["POST"])
@login_required
def update_companies(uid):
    user = User.query.get_or_404(uid)
    
    # Clear existing company assignments
    UserCompany.query.filter_by(user_id=uid).delete()
    
    # Add new company assignments
    selected_companies = request.form.getlist("companies")
    for company_id in selected_companies:
        user_company = UserCompany(
            user_id=user.id,
            company_id=company_id,
            role=request.form.get(f"role_{company_id}", "viewer")
        )
        db.session.add(user_company)
    
    db.session.commit()
    flash("Company access updated successfully!", "success")
    return redirect(url_for("users.companies", uid=uid))

@users_bp.route("/users/add_company", methods=["GET","POST"])
@login_required
def add_company():
    if not current_user.is_super_admin:
        flash("Super admin access required!", "danger")
        return redirect(url_for("users.index"))
    
    if request.method == "POST":
        company = Company(
            name=request.form["name"].strip(),
            business_type=request.form.get("business_type", "Trading"),
            gstin=request.form.get("gstin","").strip().upper() or None,
            address=request.form.get("address","").strip() or None,
            phone=request.form.get("phone","").strip() or None,
            email=request.form.get("email","").strip() or None,
            pan=request.form.get("pan","").strip().upper() or None
        )
        db.session.add(company)
        db.session.commit()
        flash("Company created successfully!", "success")
        return redirect(url_for("users.index"))
    
    return render_template("companies/form.html", company=None)

@users_bp.route("/users/edit/<int:uid>", methods=["GET","POST"])
@login_required
def edit(uid):
    cid  = session.get("company_id")
    user = User.query.filter_by(id=uid, company_id=cid).first_or_404()
    if request.method == "POST":
        user.email = request.form.get("email","").strip() or None
        user.role  = request.form.get("role","viewer")
        new_pw = request.form.get("password","").strip()
        if new_pw:
            user.password_hash = generate_password_hash(new_pw)
        db.session.commit()
        flash(f"User '{user.username}' updated!", "success")
        return redirect(url_for("users.index"))
    return render_template("users/form.html", user=user, roles=ROLES, role_desc=ROLE_DESCRIPTIONS, title="Edit User")

@users_bp.route("/users/toggle/<int:uid>", methods=["POST"])
@login_required
def toggle(uid):
    cid  = session.get("company_id")
    user = User.query.filter_by(id=uid, company_id=cid).first_or_404()
    if user.id == current_user.id:
        flash("Cannot deactivate yourself!", "danger")
    else:
        user.is_active = not user.is_active
        db.session.commit()
        status = "activated" if user.is_active else "deactivated"
        flash(f"User '{user.username}' {status}.", "info")
    return redirect(url_for("users.index"))

@users_bp.route("/users/reset-password/<int:uid>", methods=["POST"])
@login_required
def reset_password(uid):
    cid  = session.get("company_id")
    user = User.query.filter_by(id=uid, company_id=cid).first_or_404()
    new_pw = request.form.get("new_password","").strip()
    if not new_pw:
        flash("Password cannot be empty!", "danger")
    else:
        user.password_hash = generate_password_hash(new_pw)
        db.session.commit()
        flash(f"Password reset for '{user.username}'.", "success")
    return redirect(url_for("users.index"))
