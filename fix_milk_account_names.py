#!/usr/bin/env python
"""
Fix Milk Account Names - Remove " - Milk Account" suffix from account names
to maintain consistency with party names across the system.
"""

from app import create_app
from extensions import db
from models import Account, Party

def fix_milk_account_names():
    """Remove ' - Milk Account' suffix from account names and ensure consistency with parties"""
    app = create_app()
    app.app_context().push()
    
    try:
        # Find all accounts with " - Milk Account" suffix
        milk_accounts = Account.query.filter(Account.name.like('% - Milk Account')).all()
        
        print(f"Found {len(milk_accounts)} accounts to fix:")
        
        for account in milk_accounts:
            old_name = account.name
            # Remove the suffix
            new_name = old_name.replace(' - Milk Account', '')
            
            # Check if there's already an account with this name
            existing = Account.query.filter(
                Account.company_id == account.company_id,
                Account.name == new_name,
                Account.id != account.id
            ).first()
            
            if existing:
                print(f"  Skipping {old_name} -> {new_name} (already exists)")
                continue
            
            # Check if there's a party with this name
            party = Party.query.filter_by(
                company_id=account.company_id,
                name=new_name
            ).first()
            
            if not party:
                print(f"  Warning: No party found for {new_name}")
            
            # Update the account name
            account.name = new_name
            print(f"  Updated: {old_name} -> {new_name}")
        
        # Commit all changes
        db.session.commit()
        print("\n✅ All account names have been updated successfully!")
        
        # Show final state
        print("\nFinal account list:")
        all_accounts = Account.query.filter_by(company_id=1).order_by(Account.name).all()
        for acc in all_accounts:
            print(f"  {acc.name} ({acc.account_type})")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()
        raise

if __name__ == "__main__":
    fix_milk_account_names()
