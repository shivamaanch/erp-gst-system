#!/usr/bin/env python3
"""
Migration script to add bill_id column to milk_transactions table
Run this on the live PostgreSQL database
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment variables")
    sys.exit(1)

print(f"Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")

try:
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if bill_id column already exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'milk_transactions' 
            AND column_name = 'bill_id'
        """))
        
        if result.fetchone():
            print("✅ bill_id column already exists in milk_transactions table")
        else:
            print("📝 Adding bill_id column to milk_transactions table...")
            
            # Add the column
            conn.execute(text("""
                ALTER TABLE milk_transactions 
                ADD COLUMN bill_id INTEGER
            """))
            
            # Create foreign key constraint if bills table exists
            try:
                conn.execute(text("""
                    ALTER TABLE milk_transactions 
                    ADD CONSTRAINT fk_milk_transactions_bill_id 
                    FOREIGN KEY (bill_id) REFERENCES bills(id)
                """))
                print("✅ Foreign key constraint added")
            except Exception as e:
                print(f"⚠️  Could not add foreign key constraint: {e}")
            
            conn.commit()
            print("✅ bill_id column added successfully")
        
        # Verify the column exists
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'milk_transactions' 
            AND column_name = 'bill_id'
        """))
        
        row = result.fetchone()
        if row:
            print(f"✅ Column verified: {row.column_name} ({row.data_type})")
        else:
            print("❌ Column not found after migration")
            
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)

print("\n🎉 Migration completed successfully!")
