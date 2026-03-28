#!/usr/bin/env python3
"""
PostgreSQL migration script to add account_id column to cash_book table
"""

import os
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def add_cash_book_account_id_postgresql():
    """Add account_id column to cash_book table if it doesn't exist"""
    
    # Database connection parameters
    db_params = {
        'dbname': os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432')
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
            print("✅ account_id column already exists in PostgreSQL")
            return True
        
        # Add the column
        print("Adding account_id column to cash_book table in PostgreSQL...")
        cursor.execute("""
            ALTER TABLE cash_book 
            ADD COLUMN account_id INTEGER
        """)
        
        print("✅ account_id column added successfully to PostgreSQL!")
        return True
        
    except Exception as e:
        print(f"❌ Error adding column to PostgreSQL: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    add_cash_book_account_id_postgresql()
