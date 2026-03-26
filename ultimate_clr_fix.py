#!/usr/bin/env python3
"""
Ultimate CLR Column Fix - Multiple approaches
"""

import sys
import os
sys.path.insert(0,'/app')

def fix_clr_column():
    """Try multiple approaches to add CLR column"""
    
    print("=" * 60)
    print("ULTIMATE CLR COLUMN FIX")
    print("=" * 60)
    
    # Method 1: SQLAlchemy
    try:
        from app import app
        from extensions import db
        from sqlalchemy import text
        
        with app.app_context():
            print("Method 1: Using SQLAlchemy...")
            db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN clr DECIMAL(10,2) DEFAULT 0.0'))
            db.session.commit()
            print("✅ CLR column added successfully using SQLAlchemy!")
            return True
    except Exception as e:
        print(f"❌ SQLAlchemy method failed: {e}")
    
    # Method 2: Direct SQL with psycopg2
    try:
        import psycopg2
        print("Method 2: Using direct PostgreSQL connection...")
        
        # Try to get database URL from environment
        db_url = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost/erp')
        
        # Parse database URL
        if db_url.startswith('postgresql://'):
            db_url = db_url.replace('postgresql://', 'postgresql://postgres@')
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute('ALTER TABLE milk_transactions ADD COLUMN clr DECIMAL(10,2) DEFAULT 0.0')
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ CLR column added successfully using direct PostgreSQL!")
        return True
    except Exception as e:
        print(f"❌ Direct PostgreSQL method failed: {e}")
    
    # Method 3: Shell command
    try:
        import subprocess
        print("Method 3: Using shell command...")
        
        cmd = "psql -h localhost -U postgres -d erp -c 'ALTER TABLE milk_transactions ADD COLUMN clr DECIMAL(10,2) DEFAULT 0.0;'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ CLR column added successfully using shell command!")
            return True
        else:
            print(f"❌ Shell command failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Shell command method failed: {e}")
    
    print("❌ All methods failed!")
    return False

if __name__ == "__main__":
    success = fix_clr_column()
    
    if success:
        print("\n✅ CLR column fix completed successfully!")
        print("Milk entries page should work now!")
    else:
        print("\n❌ CLR column fix failed!")
        print("Manual intervention may be required.")
        print("\nTry running this manually:")
        print("psql -h localhost -U postgres -d erp -c 'ALTER TABLE milk_transactions ADD COLUMN clr DECIMAL(10,2) DEFAULT 0.0;'")
