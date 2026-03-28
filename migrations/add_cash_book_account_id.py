#!/usr/bin/env python3
"""
Migration script to add account_id column to cash_book table
"""

import sqlite3
import os

def add_cash_book_account_id():
    """Add account_id column to cash_book table if it doesn't exist"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'erp.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(cash_book)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'account_id' not in columns:
            print("Adding account_id column to cash_book table...")
            cursor.execute("""
                ALTER TABLE cash_book 
                ADD COLUMN account_id INTEGER
            """)
            conn.commit()
            print("✅ account_id column added successfully!")
        else:
            print("✅ account_id column already exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding column: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    add_cash_book_account_id()
