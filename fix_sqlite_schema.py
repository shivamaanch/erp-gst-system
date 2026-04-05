#!/usr/bin/env python3
"""
Quick script to fix SQLite milk_transactions schema by removing account_id column
"""
import os
import sqlite3
from sqlalchemy import create_engine, text

def fix_sqlite_schema():
    """Remove account_id column from milk_transactions table"""
    
    # Get database path
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'erp.db')
    
    if not os.path.exists(db_path):
        print("❌ Database file not found")
        return False
    
    print(f"🔧 Fixing SQLite schema: {db_path}")
    
    try:
        # Create engine
        engine = create_engine(f"sqlite:///{db_path}")
        
        with engine.begin() as conn:
            # Check current schema
            cols = conn.execute(text("PRAGMA table_info(milk_transactions)")).fetchall()
            col_names = [c[1] for c in cols]
            
            print(f"📋 Current columns: {col_names}")
            
            if "account_id" not in col_names:
                print("✅ account_id column already removed")
                return True
            
            # Create new table without account_id
            create_sql = """
            CREATE TABLE milk_transactions_new (
                id INTEGER PRIMARY KEY,
                company_id INTEGER NOT NULL,
                fin_year TEXT NOT NULL,
                voucher_no TEXT,
                txn_date DATE NOT NULL,
                shift TEXT DEFAULT 'Morning',
                txn_type TEXT NOT NULL,
                qty_liters NUMERIC(10,2) NOT NULL,
                fat NUMERIC(5,2) NOT NULL,
                snf NUMERIC(5,2) NOT NULL,
                clr NUMERIC(5,2) DEFAULT 0.0,
                rate NUMERIC(10,4) NOT NULL,
                amount NUMERIC(14,2) NOT NULL,
                chart_id INTEGER,
                narration TEXT,
                bill_id INTEGER
            )
            """
            
            print("🔄 Creating new table without account_id...")
            conn.execute(text(create_sql))
            
            # Copy data excluding account_id
            old_cols = [c[1] for c in cols if c[1] != "account_id"]
            cols_str = ", ".join(old_cols)
            
            print(f"📦 Copying data from columns: {old_cols}")
            conn.execute(text(f"""
                INSERT INTO milk_transactions_new ({cols_str})
                SELECT {cols_str} FROM milk_transactions
            """))
            
            # Drop old table and rename new one
            conn.execute(text("DROP TABLE milk_transactions"))
            conn.execute(text("ALTER TABLE milk_transactions_new RENAME TO milk_transactions"))
            
            print("✅ Schema fixed successfully!")
            
            # Verify new schema
            new_cols = conn.execute(text("PRAGMA table_info(milk_transactions)")).fetchall()
            new_col_names = [c[1] for c in new_cols]
            print(f"📋 New columns: {new_col_names}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error fixing schema: {e}")
        return False

if __name__ == "__main__":
    fix_sqlite_schema()
