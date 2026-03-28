#!/usr/bin/env python3
"""
Universal migration script to add missing columns to all databases
"""

import os
import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def migrate_sqlite():
    """Migrate SQLite database"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'erp.db')
    
    if not os.path.exists(db_path):
        print(f"SQLite database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check cash_book table
        cursor.execute("PRAGMA table_info(cash_book)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'account_id' not in columns:
            print("Adding account_id column to cash_book table (SQLite)...")
            cursor.execute("ALTER TABLE cash_book ADD COLUMN account_id INTEGER")
            conn.commit()
            print("✅ SQLite: account_id column added to cash_book!")
        else:
            print("✅ SQLite: account_id column already exists in cash_book")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite migration error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def migrate_postgresql():
    """Migrate PostgreSQL database"""
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
        
        # Check cash_book table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'cash_book' 
            AND column_name = 'account_id'
        """)
        
        if cursor.fetchone():
            print("✅ PostgreSQL: account_id column already exists in cash_book")
        else:
            print("Adding account_id column to cash_book table (PostgreSQL)...")
            cursor.execute("ALTER TABLE cash_book ADD COLUMN account_id INTEGER")
            print("✅ PostgreSQL: account_id column added to cash_book!")
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL migration error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Run all migrations"""
    print("🔄 Starting database migrations...")
    
    sqlite_success = migrate_sqlite()
    postgresql_success = migrate_postgresql()
    
    if sqlite_success or postgresql_success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")

if __name__ == "__main__":
    main()
