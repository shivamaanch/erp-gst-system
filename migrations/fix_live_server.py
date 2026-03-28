#!/usr/bin/env python3
"""
Quick fix for live server - add missing columns
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_live_server():
    """Add missing columns to live PostgreSQL database"""
    
    # Use environment variables for database connection
    db_params = {
        'dbname': os.getenv('POSTGRES_DB', 'postgres'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', ''),
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432')
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("🔧 Fixing live server database...")
        
        # Fix 1: Add is_active to companies table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'companies' 
            AND column_name = 'is_active'
        """)
        
        if not cursor.fetchone():
            print("Adding is_active column to companies table...")
            cursor.execute("ALTER TABLE companies ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            print("✅ Added is_active to companies")
        else:
            print("✅ is_active already exists in companies")
        
        # Fix 2: Add account_id to cash_book table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'cash_book' 
            AND column_name = 'account_id'
        """)
        
        if not cursor.fetchone():
            print("Adding account_id column to cash_book table...")
            cursor.execute("ALTER TABLE cash_book ADD COLUMN account_id INTEGER")
            print("✅ Added account_id to cash_book")
        else:
            print("✅ account_id already exists in cash_book")
        
        # Fix 3: Update existing records
        cursor.execute("UPDATE companies SET is_active = TRUE WHERE is_active IS NULL")
        print("✅ Updated companies.is_active defaults")
        
        print("🎉 Live server fixes completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing live server: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_live_server()
