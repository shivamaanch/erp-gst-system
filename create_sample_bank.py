#!/usr/bin/env python3
"""
Create a sample bank account for testing
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import BankAccount, Account

def create_sample_bank():
    """Create a sample bank account if none exists"""
    app = create_app()
    with app.app_context():
        cid = 1  # Adjust if needed for your company
        
        # Check if bank accounts already exist
        existing_banks = BankAccount.query.filter_by(company_id=cid).all()
        
        if existing_banks:
            print(f"ℹ️  Found {len(existing_banks)} existing bank accounts:")
            for bank in existing_banks:
                print(f"   - {bank.account_name} ({bank.bank_name}) - {bank.account_no}")
            return
        
        # Create a sample bank account
        bank = BankAccount(
            company_id=cid,
            account_name="Current Account",
            bank_name="State Bank of India",
            account_no="1234567890",
            ifsc="SBIN0001234",
            branch="Main Branch",
            account_type="Current",
            opening_balance=10000.00
        )
        db.session.add(bank)
        db.session.flush()
        
        # Create corresponding ledger account
        ledger_acc = Account(
            company_id=cid,
            name=f"{bank.account_name} - {bank.bank_name}",
            group_name="Bank Accounts",
            opening_dr=float(bank.opening_balance or 0),
            opening_cr=0,
            is_active=True
        )
        db.session.add(ledger_acc)
        db.session.flush()  # Get the ledger account ID
        
        # Link bank account to ledger account
        bank.account_id = ledger_acc.id
        
        db.session.commit()
        
        print(f"✅ Created sample bank account: {bank.account_name}")
        print(f"   Bank: {bank.bank_name}")
        print(f"   Account No: {bank.account_no}")
        print(f"   Opening Balance: ₹{bank.opening_balance:,.2f}")
        print(f"\n✅ Created corresponding ledger account: {ledger_acc.name}")

if __name__ == "__main__":
    print("🚀 Creating sample bank account...")
    create_sample_bank()
    print("\n✅ Done! You can now use Quick Bank Entry.")
