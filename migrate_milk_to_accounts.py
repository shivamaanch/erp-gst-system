#!/usr/bin/env python3
"""
Migration script: Convert MilkTransaction from party_id to account_id
This script will:
1. Backup existing MilkTransaction data
2. Create ledger accounts for all parties
3. Update MilkTransaction records to use account_id
4. Remove party_id column
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import MilkTransaction, Party, Account, Company
from datetime import datetime
import json

def backup_data():
    """Backup current MilkTransaction data to JSON"""
    print("📦 Backing up MilkTransaction data...")
    
    transactions = MilkTransaction.query.all()
    backup = []
    
    for txn in transactions:
        backup.append({
            'id': txn.id,
            'company_id': txn.company_id,
            'fin_year': txn.fin_year,
            'voucher_no': txn.voucher_no,
            'party_id': txn.party_id,
            'txn_date': txn.txn_date.isoformat() if txn.txn_date else None,
            'shift': txn.shift,
            'txn_type': txn.txn_type,
            'qty_liters': float(txn.qty_liters),
            'fat': float(txn.fat),
            'snf': float(txn.snf),
            'clr': float(txn.clr) if txn.clr else 0.0,
            'rate': float(txn.rate),
            'amount': float(txn.amount),
            'chart_id': txn.chart_id,
            'narration': txn.narration,
            'bill_id': txn.bill_id
        })
    
    with open('milk_transactions_backup.json', 'w') as f:
        json.dump(backup, f, indent=2, default=str)
    
    print(f"✅ Backed up {len(backup)} MilkTransaction records")

def create_accounts_for_parties():
    """Create ledger accounts for all parties"""
    print("🏗️ Creating ledger accounts for parties...")
    
    companies = Company.query.all()
    accounts_created = 0
    
    for company in companies:
        parties = Party.query.filter_by(company_id=company.id, is_active=True).all()
        
        for party in parties:
            # Check if account already exists
            existing_account = Account.query.filter_by(
                company_id=company.id, 
                name=party.name
            ).first()
            
            if not existing_account:
                # Create ledger account for the party
                account = Account(
                    company_id=company.id,
                    name=party.name,
                    group_name="Sundry Debtors",  # Default group
                    opening_dr=party.opening_balance if party.balance_type == "Dr" else 0,
                    opening_cr=party.opening_balance if party.balance_type == "Cr" else 0,
                    is_active=True
                )
                db.session.add(account)
                accounts_created += 1
                print(f"  ✅ Created account: {party.name}")
            else:
                print(f"  ⚠️ Account already exists: {party.name}")
    
    db.session.commit()
    print(f"✅ Created {accounts_created} new ledger accounts")

def update_milk_transactions():
    """Update MilkTransaction records to use account_id instead of party_id"""
    print("🔄 Updating MilkTransaction records...")
    
    updated = 0
    failed = 0
    
    transactions = MilkTransaction.query.all()
    
    for txn in transactions:
        try:
            # Find the party
            party = Party.query.get(txn.party_id)
            if not party:
                print(f"  ❌ Party not found for transaction {txn.id}")
                failed += 1
                continue
            
            # Find the corresponding account
            account = Account.query.filter_by(
                company_id=txn.company_id,
                name=party.name
            ).first()
            
            if not account:
                print(f"  ❌ Account not found for party {party.name}")
                failed += 1
                continue
            
            # Update the transaction
            txn.account_id = account.id
            updated += 1
            
        except Exception as e:
            print(f"  ❌ Error updating transaction {txn.id}: {e}")
            failed += 1
    
    db.session.commit()
    print(f"✅ Updated {updated} MilkTransaction records")
    print(f"❌ Failed to update {failed} records")

def main():
    """Main migration function"""
    print("🚀 Starting MilkTransaction to Account migration...")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Backup data
            backup_data()
            
            # Step 2: Create accounts for parties
            create_accounts_for_parties()
            
            # Step 3: Update transactions
            update_milk_transactions()
            
            print("=" * 60)
            print("✅ Migration completed successfully!")
            print("📝 Backup saved to: milk_transactions_backup.json")
            print("⚠️  IMPORTANT: Run 'flask db upgrade' to remove party_id column")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    main()
