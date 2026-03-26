#!/usr/bin/env python3
"""
Manual fix for parties table missing columns
Run this in Northflank shell if automatic migration fails
"""

import os
import psycopg2
import urllib.parse

def fix_parties_table():
    """Fix missing columns in parties table"""
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
        
        cursor = conn.cursor()
        print("🔧 Fixing parties table...")
        
        # Check and add opening_balance column
        try:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'parties' AND column_name = 'opening_balance'
            """)
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE parties ADD COLUMN opening_balance DECIMAL(18,2) DEFAULT 0.00")
                print("✅ Added opening_balance column to parties")
            else:
                print("✅ opening_balance column already exists")
        except Exception as e:
            print(f"⚠️  opening_balance column issue: {e}")
        
        # Check and add balance_type column
        try:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'parties' AND column_name = 'balance_type'
            """)
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE parties ADD COLUMN balance_type VARCHAR(2) DEFAULT 'Dr'")
                print("✅ Added balance_type column to parties")
            else:
                print("✅ balance_type column already exists")
        except Exception as e:
            print(f"⚠️  balance_type column issue: {e}")
        
        # Update defaults
        try:
            cursor.execute("UPDATE parties SET opening_balance = 0.00 WHERE opening_balance IS NULL")
            cursor.execute("UPDATE parties SET balance_type = 'Dr' WHERE balance_type IS NULL")
            print("✅ Updated parties table defaults")
        except Exception as e:
            print(f"⚠️  Error updating defaults: {e}")
        
        conn.commit()
        conn.close()
        print("🎉 Parties table fix completed!")
        return True
        
    except Exception as e:
        print(f"❌ Fix error: {e}")
        return False

if __name__ == "__main__":
    fix_parties_table()
