#!/usr/bin/env python3
"""
Live server migration script for Northflank deployment
Run this script on the live server to add missing columns
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def add_cash_book_account_id():
    """Add account_id column to cash_book table in PostgreSQL"""
    
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
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'cash_book' 
            AND column_name = 'account_id'
        """)
        
        if cursor.fetchone():
            print("✅ account_id column already exists in cash_book")
            return True
        
        # Add the column
        print("Adding account_id column to cash_book table...")
        cursor.execute("ALTER TABLE cash_book ADD COLUMN account_id INTEGER")
        
        print("✅ account_id column added successfully to cash_book!")
        
        # Also check if we need to add the relationship
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'cash_book' 
            AND column_name = 'account_id'
        """)
        
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error adding column: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    add_cash_book_account_id()
