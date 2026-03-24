# modules/permissions.py
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def require_role(*roles):
    """
    Decorator to enforce role-based access control
    Usage: @require_role("Admin", "Manager")
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                flash("Access denied. Insufficient permissions.", "danger")
                return redirect(url_for("reports.hub"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_only(f):
    """Shortcut decorator for admin-only routes"""
    return require_role("Admin")(f)

def can_edit(f):
    """Decorator for routes that require edit permissions (Admin, Manager, Accountant, Staff)"""
    return require_role("Admin", "Manager", "Accountant", "Staff")(f)

def can_view_reports(f):
    """Decorator for report viewing (all roles)"""
    return require_role("Admin", "Manager", "Accountant", "Staff", "Viewer")(f)
