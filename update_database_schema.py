#!/usr/bin/env python3
"""
Database schema update script
This script will update the database schema to match the new models
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import MilkTransaction
from sqlalchemy import text

def update_milk_transactions_schema():
    """Update milk_transactions table schema"""
    print("🔧 Updating milk_transactions table schema...")
    
    with create_app().app_context():
        try:
            # Check if account_id column exists
            result = db.session.execute(text("PRAGMA table_info(milk_transactions)"))
            columns = [row[1] for row in result.fetchall()]
            
            print(f"Current columns: {columns}")
            
            if 'account_id' not in columns:
                print("➕ Adding account_id column...")
                # Add account_id column
                db.session.execute(text("""
                    ALTER TABLE milk_transactions 
                    ADD COLUMN account_id INTEGER
                """))
                
                # Update existing records with account_id based on party_id
                print("🔄 Migrating data from party_id to account_id...")
                db.session.execute(text("""
                    UPDATE milk_transactions 
                    SET account_id = (
                        SELECT a.id 
                        FROM accounts a 
                        WHERE a.name = (
                            SELECT p.name 
                            FROM parties p 
                            WHERE p.id = milk_transactions.party_id
                        )
                        AND a.company_id = milk_transactions.company_id
                    )
                    WHERE party_id IS NOT NULL
                """))
                
                # Make account_id NOT NULL after data migration
                print("✅ Making account_id required...")
                db.session.execute(text("""
                    UPDATE milk_transactions 
                    SET account_id = 1 
                    WHERE account_id IS NULL
                """))
                
                db.session.commit()
                print("✅ Schema update completed!")
            else:
                print("ℹ️ account_id column already exists")
                
        except Exception as e:
            print(f"❌ Schema update failed: {e}")
            db.session.rollback()
            raise

def check_milk_transactions():
    """Check milk_transactions after schema update"""
    print("\n🔍 Checking milk_transactions...")
    
    with create_app().app_context():
        try:
            # Test query
            txn = MilkTransaction.query.first()
            if txn:
                print(f"✅ First transaction account_id: {txn.account_id}")
                print(f"✅ First transaction company_id: {txn.company_id}")
                
                # Count total
                total = MilkTransaction.query.count()
                print(f"✅ Total transactions: {total}")
                
                # Check all have account_id
                null_count = db.session.execute(text(
                    "SELECT COUNT(*) FROM milk_transactions WHERE account_id IS NULL"
                )).scalar()
                
                if null_count == 0:
                    print("✅ All transactions have account_id")
                else:
                    print(f"⚠️ {null_count} transactions missing account_id")
            else:
                print("ℹ️ No transactions found")
                
        except Exception as e:
            print(f"❌ Check failed: {e}")

def main():
    """Main function"""
    print("🚀 Starting database schema update...")
    print("=" * 60)
    
    try:
        update_milk_transactions_schema()
        check_milk_transactions()
        
        print("=" * 60)
        print("✅ Database schema update completed successfully!")
        
    except Exception as e:
        print(f"❌ Database update failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
