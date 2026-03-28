#!/usr/bin/env python3
"""
Complete live server migration script for Northflank deployment
This script adds all missing columns to PostgreSQL database
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def get_db_connection():
    """Get database connection using environment variables"""
    return {
        'dbname': os.getenv('POSTGRES_DB', 'postgres'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', ''),
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432')
    }

def check_and_add_column(cursor, table_name, column_name, column_definition):
    """Check if column exists and add it if it doesn't"""
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s 
        AND column_name = %s
    """, (table_name, column_name))
    
    if cursor.fetchone():
        print(f"✅ Column {column_name} already exists in {table_name}")
        return True
    else:
        print(f"Adding {column_name} column to {table_name} table...")
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
            print(f"✅ Column {column_name} added to {table_name}!")
            return True
        except Exception as e:
            print(f"❌ Error adding column {column_name} to {table_name}: {e}")
            return False

def run_migrations():
    """Run all necessary migrations"""
    db_params = get_db_connection()
    
    try:
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("🔄 Starting live server migrations...")
        
        # Migration 1: Add account_id to cash_book table
        success1 = check_and_add_column(
            cursor, 
            'cash_book', 
            'account_id', 
            'INTEGER'
        )
        
        # Migration 2: Add is_active to companies table
        success2 = check_and_add_column(
            cursor, 
            'companies', 
            'is_active', 
            'BOOLEAN DEFAULT TRUE'
        )
        
        # Migration 3: Add foreign key constraint for cash_book.account_id (if accounts table exists)
        try:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'accounts'
            """)
            if cursor.fetchone():
                print("Adding foreign key constraint for cash_book.account_id...")
                try:
                    cursor.execute("""
                        ALTER TABLE cash_book 
                        ADD CONSTRAINT fk_cash_book_account 
                        FOREIGN KEY (account_id) REFERENCES accounts(id)
                    """)
                    print("✅ Foreign key constraint added!")
                except Exception as e:
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print("✅ Foreign key constraint already exists")
                    else:
                        print(f"⚠️ Could not add foreign key constraint: {e}")
        except Exception as e:
            print(f"⚠️ Could not check accounts table: {e}")
        
        if success1 and success2:
            print("🎉 All migrations completed successfully!")
            return True
        else:
            print("❌ Some migrations failed")
            return False
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_migrations()
