#!/usr/bin/env python3
"""
Debug script to check accounts creation
"""

from app import app
from models import Account, Company
from extensions import db

def check_accounts():
    with app.app_context():
        print("=" * 50)
        print("ACCOUNTS DEBUG CHECK")
        print("=" * 50)
        
        # Check companies
        companies = Company.query.all()
        print(f"Total companies: {len(companies)}")
        for comp in companies:
            print(f"  - {comp.name} (ID: {comp.id})")
        
        print("\n" + "=" * 50)
        
        # Check accounts for each company
        for company in companies:
            print(f"\nAccounts for {company.name} (ID: {company.id}):")
            accounts = Account.query.filter_by(company_id=company.id, is_active=True).all()
            print(f"  Total accounts: {len(accounts)}")
            
            if accounts:
                # Group by group_name
                groups = {}
                for acc in accounts:
                    group = acc.group_name or "No Group"
                    if group not in groups:
                        groups[group] = []
                    groups[group].append(acc)
                
                for group_name, accs in groups.items():
                    print(f"    {group_name}: {len(accs)} accounts")
                    for acc in accs[:3]:  # Show first 3 accounts per group
                        print(f"      - {acc.name}")
                    if len(accs) > 3:
                        print(f"      ... and {len(accs)-3} more")
            else:
                print("    No accounts found!")
        
        print("\n" + "=" * 50)
        print("DEBUG COMPLETE")
        print("=" * 50)

if __name__ == "__main__":
    check_accounts()
