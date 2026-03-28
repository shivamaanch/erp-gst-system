#!/usr/bin/env python3
"""
Emergency fix for live server - adds missing columns before app starts
Run this script directly to fix the database
"""

import os
import psycopg2
import urllib.parse
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def emergency_fix():
    """Add missing columns to live PostgreSQL database before app starts"""
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found!")
        return False
    
    try:
        parsed = urllib.parse.urlparse(db_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("🔧 Running emergency database fix...")
        
        # Critical fixes needed for app to start
        critical_fixes = [
            ("companies", "is_active", "BOOLEAN DEFAULT TRUE"),
            ("cash_book", "account_id", "INTEGER"),
        ]
        
        for table_name, col_name, col_type in critical_fixes:
            try:
                cursor.execute(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = '{table_name}' AND column_name = '{col_name}'
                """)
                if not cursor.fetchone():
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                    print(f"✅ Added {col_name} to {table_name}")
                else:
                    print(f"✅ {col_name} already exists in {table_name}")
            except Exception as e:
                print(f"❌ Error adding {col_name} to {table_name}: {e}")
        
        # Update existing records
        cursor.execute("UPDATE companies SET is_active = TRUE WHERE is_active IS NULL")
        print("✅ Updated companies.is_active defaults")
        
        print("🎉 Emergency fix completed!")
        return True
        
    except Exception as e:
        print(f"❌ Emergency fix failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    emergency_fix()
