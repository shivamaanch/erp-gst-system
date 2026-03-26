#!/usr/bin/env python3
"""
Direct CLR Fix - Run this file directly in Northflank container
"""

import sys
sys.path.insert(0,'/app')

try:
    from app import app
    from extensions import db
    from sqlalchemy import text
    
    with app.app_context():
        print("Adding CLR column to milk_transactions table...")
        
        # Add CLR column
        result = db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN clr DECIMAL(10,2) DEFAULT 0.0'))
        db.session.commit()
        
        print("✅ CLR column added successfully!")
        print("Milk entries page should work now!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("CLR column might already exist or there's another issue")
