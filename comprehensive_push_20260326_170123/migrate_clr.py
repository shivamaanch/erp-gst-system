#!/usr/bin/env python3
"""
Simple SQLite migration to add CLR column
"""

import sqlite3
import os
import glob

def find_database():
    """Find the SQLite database file"""
    # Common database names
    patterns = ['*.db', '*.sqlite', '*.sqlite3']
    
    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            return files[0]
    
    # Check subdirectories
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.db', '.sqlite', '.sqlite3')):
                return os.path.join(root, file)
    
    return None

def add_clr_column():
    db_path = find_database()
    
    if not db_path:
        print("No database file found")
        return False
    
    print(f"Using database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(milk_transactions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'clr' in columns:
            print("CLR column already exists")
            conn.close()
            return True
        
        # Add the column
        cursor.execute("ALTER TABLE milk_transactions ADD COLUMN clr NUMERIC(5,2) DEFAULT 0.0")
        conn.commit()
        
        print("CLR column added successfully")
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    add_clr_column()
