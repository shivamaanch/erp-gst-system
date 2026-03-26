#!/usr/bin/env python3
"""
Database Migration Script
Run this to fix missing database columns
"""

import sys
import os

def run_migration():
    """Run database migration to fix missing columns"""
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(__file__))
        
        from app import app
        from extensions import db
        from sqlalchemy import text
        
        with app.app_context():
            print("Starting database migration...")
            
            # Add voucher_no to bills table
            try:
                result = db.session.execute(text('ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50)'))
                db.session.commit()
                print("✅ Added voucher_no to bills table")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e):
                    print("✅ voucher_no already exists in bills table")
                else:
                    print(f"❌ Error adding voucher_no to bills: {e}")
                    db.session.rollback()
            
            # Add voucher_no to milk_transactions table
            try:
                result = db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50)'))
                db.session.commit()
                print("✅ Added voucher_no to milk_transactions table")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e):
                    print("✅ voucher_no already exists in milk_transactions table")
                else:
                    print(f"❌ Error adding voucher_no to milk_transactions: {e}")
                    db.session.rollback()
            
            # Add CLR column to milk_transactions table
            try:
                result = db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN clr DECIMAL(10,2) DEFAULT 0.0'))
                db.session.commit()
                print("✅ Added CLR column to milk_transactions table")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e):
                    print("✅ CLR column already exists in milk_transactions table")
                else:
                    print(f"❌ Error adding CLR column to milk_transactions: {e}")
                    db.session.rollback()
            
            # Add created_at to gstr2b_records table
            try:
                result = db.session.execute(text('ALTER TABLE gstr2b_records ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))
                db.session.commit()
                print("✅ Added created_at to gstr2b_records table")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e):
                    print("✅ created_at already exists in gstr2b_records table")
                else:
                    print(f"❌ Error adding created_at to gstr2b_records: {e}")
                    db.session.rollback()
            
            print("✅ Database migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("DATABASE MIGRATION SCRIPT")
    print("=" * 60)
    print("This script fixes missing database columns:")
    print("• voucher_no column in bills table")
    print("• voucher_no column in milk_transactions table") 
    print("• CLR column in milk_transactions table")
    print("• created_at column in gstr2b_records table")
    print()
    
    success = run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("Application should start without database errors now.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above.")
    
    print("\nTo run this on Northflank:")
    print("1. SSH into the container")
    print("2. Run: python migrate_database.py")
    print("3. Restart the application")

if __name__ == "__main__":
    main()
