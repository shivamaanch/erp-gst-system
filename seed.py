from app import create_app
from extensions import db
from models import User, Company, FinancialYear
from datetime import date
import bcrypt

app = create_app()
with app.app_context():
    db.create_all()
    company = Company(name="My Company", gstin="29AABCT1332L1ZV",
                      state_code="29", address="Your Address, City")
    db.session.add(company); db.session.flush()
    fy = FinancialYear(company_id=company.id, year_name="2025-26",
                       start_date=date(2025,4,1), end_date=date(2026,3,31), is_active=True)
    db.session.add(fy); db.session.flush()
    pw = bcrypt.hashpw(b"admin@123", bcrypt.gensalt()).decode()
    admin = User(company_id=company.id, username="admin",
                 email="admin@example.com", password_hash=pw, role="Admin")
    db.session.add(admin)
    db.session.commit()
    print("✅ Seeded: admin / admin@123")
