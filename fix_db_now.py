#!/usr/bin/env python3
"""
Quick database fix - run this in the container
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("ERROR: DATABASE_URL not found")
    exit(1)

import urllib.parse
parsed = urllib.parse.urlparse(db_url)

try:
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    print("🔧 Fixing database...")
    
    # Fix 1: Add is_active to companies
    cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'companies' AND column_name = 'is_active'
    """)
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE companies ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
        cursor.execute("UPDATE companies SET is_active = TRUE")
        print("✅ Added is_active to companies")
    else:
        print("✅ is_active already exists")
    
    # Fix 2: Add account_id to cash_book
    cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'cash_book' AND column_name = 'account_id'
    """)
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE cash_book ADD COLUMN account_id INTEGER")
        print("✅ Added account_id to cash_book")
    else:
        print("✅ account_id already exists")
    
    conn.close()
    print("🎉 Database fixed! Now restart the service.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
