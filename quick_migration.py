#!/usr/bin/env python3
"""
Quick Migration for Northflank - Run in Shell
"""

import os
from flask import Flask
from extensions import db
from models import User, Company, FinancialYear, UserCompany, CompanyAccessLog
from dotenv import load_dotenv

load_dotenv()

def quick_migrate():
    """Quick migration using Flask app context"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    db.init_app(app)
    
    with app.app_context():
        try:
            print("🔄 Starting quick migration...")
            
            # Create tables
            db.create_all()
            print("✅ Created all tables")
            
            # Check if is_super_admin column exists
            try:
                db.session.execute("SELECT is_super_admin FROM users LIMIT 1")
                print("✅ is_super_admin column exists")
            except:
                try:
                    db.session.execute("ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE")
                    print("✅ Added is_super_admin column")
                except:
                    print("⚠️  is_super_admin column might already exist")
            
            # Update first user to super admin
            user = User.query.first()
            if user:
                user.is_super_admin = True
                print("✅ Updated first user to super admin")
            else:
                print("⚠️  No users found")
            
            # Migrate user-company relationships
            users_with_company = User.query.filter(User.company_id.isnot(None)).all()
            for user in users_with_company:
                existing = UserCompany.query.filter_by(
                    user_id=user.id, 
                    company_id=user.company_id
                ).first()
                if not existing:
                    uc = UserCompany(
                        user_id=user.id,
                        company_id=user.company_id,
                        role=user.role or 'admin'
                    )
                    db.session.add(uc)
            print("✅ Migrated user-company relationships")
            
            db.session.commit()
            print("🎉 Migration completed successfully!")
            
            # Show summary
            user_count = User.query.count()
            company_count = Company.query.count()
            uc_count = UserCompany.query.count()
            
            print(f"\n📊 Database Summary:")
            print(f"  Users: {user_count}")
            print(f"  Companies: {company_count}")
            print(f"  User-Company Relationships: {uc_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    quick_migrate()
