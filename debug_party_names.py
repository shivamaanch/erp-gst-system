#!/usr/bin/env python3
"""
Debug script to check party names in milk_transactions
"""
import os
import sqlite3
from sqlalchemy import create_engine, text

def debug_party_names():
    """Check party names in milk_transactions table"""
    
    # Get database path
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'erp.db')
    
    if not os.path.exists(db_path):
        print("❌ Database file not found")
        return
    
    print(f"🔍 Debugging party names in: {db_path}")
    
    try:
        # Create engine
        engine = create_engine(f"sqlite:///{db_path}")
        
        with engine.begin() as conn:
            # Get recent milk transactions
            result = conn.execute(text("""
                SELECT id, txn_date, shift, txn_type, qty_liters, fat, narration, bill_id
                FROM milk_transactions 
                WHERE txn_type = 'Purchase' 
                ORDER BY txn_date DESC, id DESC 
                LIMIT 5
            """))
            
            rows = result.fetchall()
            
            print(f"\n📊 Recent Milk Purchase Transactions:")
            print("=" * 80)
            
            for row in rows:
                print(f"ID: {row.id}")
                print(f"Date: {row.txn_date}")
                print(f"Shift: {row.shift}")
                print(f"Type: {row.txn_type}")
                print(f"Qty: {row.qty_liters}L")
                print(f"FAT: {row.fat}%")
                print(f"Narration: {row.narration}")
                print(f"Bill ID: {row.bill_id}")
                
                # Extract party name
                party_name = "Unknown"
                if row.narration and "Party:" in row.narration:
                    parts = row.narration.split("|")
                    for part in parts:
                        if "Party:" in part:
                            party_name = part.split("Party:")[1].strip()
                            break
                
                print(f"👤 Extracted Party: {party_name}")
                print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_party_names()
