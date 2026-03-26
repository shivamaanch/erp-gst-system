#!/usr/bin/env python3
"""
Direct Database Fix Script
"""

import sys
import os

sys.path.insert(0, '/app')

try:
    from app import app
    from extensions import db
    from sqlalchemy import text
    
    with app.app_context():
        print("Starting database fix...")
        
        # Fix bills table
        try:
            result = db.session.execute(text('ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50)'))
            db.session.commit()
            print("SUCCESS: Added voucher_no to bills table")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e):
                print("INFO: voucher_no already exists in bills table")
            else:
                print(f"ERROR adding voucher_no to bills: {e}")
                db.session.rollback()
        
        # Fix milk_transactions table
        try:
            result = db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50)'))
            db.session.commit()
            print("SUCCESS: Added voucher_no to milk_transactions table")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e):
                print("INFO: voucher_no already exists in milk_transactions table")
            else:
                print(f"ERROR adding voucher_no to milk_transactions: {e}")
                db.session.rollback()
        
        print("Database fix completed successfully!")
        print("Application should start without errors now.")
        
except Exception as e:
    print(f"FATAL ERROR: {e}")
    print("Database fix failed!")
    import traceback
    traceback.print_exc()
    
    print("\\nManual fix required:")
    print("1. Connect to PostgreSQL database")
    print("2. Run: ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50)")
    print("3. Run: ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50)")
