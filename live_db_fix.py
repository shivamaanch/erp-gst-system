#!/usr/bin/env python3
"""
Database Fix for Live Environment
Adds missing voucher_no columns
"""

import sys
sys.path.insert(0, '/app')

try:
    from app import app
    from extensions import db
    from sqlalchemy import text
    
    with app.app_context():
        print("Starting database fix...")
        
        # Add voucher_no to bills table
        try:
            db.session.execute(text('ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50)'))
            db.session.commit()
            print("Added voucher_no to bills table")
        except Exception as e:
            print(f"bills.voucher_no issue: {e}")
            db.session.rollback()
        
        # Add voucher_no to milk_transactions table
        try:
            db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50)'))
            db.session.commit()
            print("Added voucher_no to milk_transactions table")
        except Exception as e:
            print(f"milk_transactions.voucher_no issue: {e}")
            db.session.rollback()
        
        print("Database fix completed!")
        
except Exception as e:
    print(f"Fix failed: {e}")
    import traceback
    traceback.print_exc()
