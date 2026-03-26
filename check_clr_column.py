#!/usr/bin/env python3
"""
Check if CLR column exists in milk_transactions table
"""

import sys
sys.path.insert(0,'/app')

try:
    from app import app
    from extensions import db
    from sqlalchemy import text
    
    with app.app_context():
        print("Checking if CLR column exists in milk_transactions table...")
        
        # Check if CLR column exists
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'milk_transactions' 
            AND column_name = 'clr'
        """))
        
        if result.fetchone():
            print("✅ CLR column exists in milk_transactions table!")
        else:
            print("❌ CLR column does not exist in milk_transactions table")
            print("Running direct fix...")
            
            # Add CLR column
            try:
                db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN clr DECIMAL(10,2) DEFAULT 0.0'))
                db.session.commit()
                print("✅ CLR column added successfully!")
            except Exception as e:
                print(f"❌ Error adding CLR column: {e}")
                db.session.rollback()
        
except Exception as e:
    print(f"❌ Error checking CLR column: {e}")
