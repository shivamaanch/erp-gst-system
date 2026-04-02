#!/usr/bin/env python3
"""
Create ledger accounts for existing bank accounts that don't have them
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import BankAccount, Account

def create_bank_ledger_accounts():
    """Create ledger accounts for bank accounts that don't have them"""
    app = create_app()
    with app.app_context():
        cid = 1  # Adjust if needed for your company
        
        # Get all bank accounts
        bank_accounts = BankAccount.query.filter_by(company_id=cid).all()
        
        created_count = 0
        for bank in bank_accounts:
            # Check if ledger account already exists
            existing = Account.query.filter_by(
                company_id=cid,
                name=f"{bank.account_name} - {bank.bank_name}"
            ).first()
            
            if not existing:
                # Create ledger account
                ledger_acc = Account(
                    company_id=cid,
                    name=f"{bank.account_name} - {bank.bank_name}",
                    group_name="Bank Accounts",
                    opening_dr=float(bank.opening_balance or 0),
                    opening_cr=0,
                    is_active=True
                )
                db.session.add(ledger_acc)
                created_count += 1
                print(f"✅ Created ledger account for: {bank.account_name}")
            else:
                print(f"ℹ️  Ledger account already exists for: {bank.account_name}")
        
        if created_count > 0:
            db.session.commit()
            print(f"\n✅ Created {created_count} new ledger accounts for banks")
        else:
            print(f"\nℹ️  All bank accounts already have ledger accounts")

if __name__ == "__main__":
    print("🚀 Creating ledger accounts for bank accounts...")
    create_bank_ledger_accounts()
    print("\n✅ Migration completed!")
