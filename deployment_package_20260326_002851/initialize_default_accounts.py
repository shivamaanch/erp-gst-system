#!/usr/bin/env python3
"""
Initialize Default Chart of Accounts for All Companies
Run this script to create default accounts for existing companies
"""

from app import app
from extensions import db
from models import Company
from utils.default_accounts import create_default_accounts

def initialize_all_companies():
    """Create default accounts for all existing companies"""
    with app.app_context():
        companies = Company.query.all()
        
        print(f"Found {len(companies)} companies")
        print("=" * 50)
        
        for company in companies:
            print(f"\nProcessing: {company.name} (ID: {company.id})")
            try:
                count = create_default_accounts(company.id)
                print(f"✅ Created {count} default accounts")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n" + "=" * 50)
        print("✅ Initialization complete!")

if __name__ == "__main__":
    initialize_all_companies()
