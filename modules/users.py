# modules/users.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

users_bp = Blueprint("users", __name__)
ROLES = ["admin", "accountant", "viewer"]

@users_bp.route("/users")
@login_required
def index():
    cid   = session.get("company_id")
    users = User.query.filter_by(company_id=cid).order_by(User.username).all()
    return render_template("users/index.html", users=users, roles=ROLES)

@users_bp.route("/users/add", methods=["GET","POST"])
@login_required
def add():
    cid = session.get("company_id")
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        role     = request.form.get("role","viewer")
        email    = request.form.get("email","").strip() or None
        if User.query.filter_by(username=username).first():
            flash(f"Username '{username}' already taken!", "danger")
            return render_template("users/form.html", user=None, roles=ROLES, title="Add User")
        u = User(
            company_id    = cid,
            username      = username,
            email         = email,
            role          = role,
            is_active     = True,
            password_hash = generate_password_hash(password)
        )
        db.session.add(u)
        db.session.commit()
        flash(f"User '{username}' created!", "success")
        return redirect(url_for("users.index"))
    return render_template("users/form.html", user=None, roles=ROLES, title="Add User")

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
    return render_template("users/form.html", user=user, roles=ROLES, title="Edit User")

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
