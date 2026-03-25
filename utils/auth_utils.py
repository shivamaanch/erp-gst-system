# utils/auth_utils.py
from functools import wraps
from flask import current_app, session
from flask_login import login_required, current_user

def optional_login_required(f):
    """
    Custom decorator that bypasses login requirement if DISABLE_LOGIN is True
    Used for temporary deployment testing on Northflank
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_app.config.get('DISABLE_LOGIN', False):
            # Auto-login as first user if login is disabled
            if not current_user.is_authenticated:
                from models import User, Company, FinancialYear
                user = User.query.first()
                if user:
                    from flask_login import login_user
                    login_user(user)
                    
                    # Set up session for first company
                    company = Company.query.first()
                    if company:
                        fy = FinancialYear.query.filter_by(company_id=company.id, is_active=True).first()
                        session["company_id"] = company.id
                        session["company_name"] = company.name
                        session["fin_year"] = fy.year_name if fy else "2025-26"
                        session["user_role"] = "admin"
            return f(*args, **kwargs)
        else:
            # Use normal login_required if login is not disabled
            return login_required(f)(*args, **kwargs)
    return decorated_function
