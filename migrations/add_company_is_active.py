#!/usr/bin/env python3
"""
Migration script to add is_active column to companies table
"""

import os
import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def add_company_is_active_sqlite():
    """Add is_active column to companies table in SQLite"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'erp.db')
    
    if not os.path.exists(db_path):
        print(f"SQLite database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(companies)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_active' not in columns:
            print("Adding is_active column to companies table (SQLite)...")
            cursor.execute("ALTER TABLE companies ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            conn.commit()
            print("✅ SQLite: is_active column added to companies!")
        else:
            print("✅ SQLite: is_active column already exists in companies")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite migration error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def add_company_is_active_postgresql():
    """Add is_active column to companies table in PostgreSQL"""
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
            WHERE table_name = 'companies' 
            AND column_name = 'is_active'
        """)
        
        if cursor.fetchone():
            print("✅ PostgreSQL: is_active column already exists in companies")
        else:
            print("Adding is_active column to companies table (PostgreSQL)...")
            cursor.execute("ALTER TABLE companies ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            print("✅ PostgreSQL: is_active column added to companies!")
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL migration error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Run all migrations for is_active column"""
    print("🔄 Adding is_active column to companies table...")
    
    sqlite_success = add_company_is_active_sqlite()
    postgresql_success = add_company_is_active_postgresql()
    
    if sqlite_success or postgresql_success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")

if __name__ == "__main__":
    main()
