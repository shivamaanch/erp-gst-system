#!/usr/bin/env python3
"""
Northflank Complete Fix
"""

import sys
sys.path.insert(0, '/app')

try:
    from app import app
    from extensions import db
    from sqlalchemy import text
    
    with app.app_context():
        print("Starting Northflank fix...")
        
        # Add voucher_no to bills
        try:
            db.session.execute(text('ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50)'))
            db.session.commit()
            print("Added voucher_no to bills")
        except:
            print("voucher_no already exists in bills")
        
        # Add voucher_no to milk_transactions
        try:
            db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50)'))
            db.session.commit()
            print("Added voucher_no to milk_transactions")
        except:
            print("voucher_no already exists in milk_transactions")
        
        # Create indexes
        try:
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_bills_voucher_no ON bills(voucher_no)'))
            db.session.commit()
            print("Created bills.voucher_no index")
        except:
            print("bills.voucher_no index issue")
        
        try:
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_milk_transactions_voucher_no ON milk_transactions(voucher_no)'))
            db.session.commit()
            print("Created milk_transactions.voucher_no index")
        except:
            print("milk_transactions.voucher_no index issue")
        
        print("Fix completed! Application should start now.")
        
except Exception as e:
    print(f"Fix failed: {e}")
    print("Try manual SQL:")
    print("ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50);")
    print("ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50);")
