#!/usr/bin/env python3
"""
Migration script to add CLR column to milk_transactions table
"""

import sqlite3
import os

def add_clr_column():
    # Try to find database file
    db_path = None
    possible_names = ['erp.db', 'database.db', 'app.db', 'instance/erp.db']
    
    for name in possible_names:
        path = os.path.join(os.path.dirname(__file__), name)
        if os.path.exists(path):
            db_path = path
            break
    
    if db_path is None:
        print("Database file not found. Please run this through Flask app instead.")
        print("Try: python -c \"from add_clr_column import add_clr_column_via_flask; add_clr_column_via_flask()\"")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if CLR column already exists
        cursor.execute("PRAGMA table_info(milk_transactions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'clr' in columns:
            print("CLR column already exists")
            conn.close()
            return True
        
        # Add CLR column
        cursor.execute("ALTER TABLE milk_transactions ADD COLUMN clr NUMERIC(5,2) DEFAULT 0.0")
        conn.commit()
        
        print("CLR column added successfully")
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error adding CLR column: {e}")
        return False

def add_clr_column_via_flask():
    """Add CLR column using Flask app context"""
    try:
        from app import create_app
        from models import db
        
        app = create_app()
        with app.app_context():
            # Check if CLR column exists
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('milk_transactions')
            column_names = [col['name'] for col in columns]
            
            if 'clr' in column_names:
                print("CLR column already exists")
                return True
            
            # Add CLR column using raw SQL
            db.engine.execute('ALTER TABLE milk_transactions ADD COLUMN clr NUMERIC(5,2) DEFAULT 0.0')
            db.session.commit()
            print("CLR column added successfully via Flask")
            return True
            
    except Exception as e:
        print(f"Error adding CLR column via Flask: {e}")
        return False

if __name__ == "__main__":
    if not add_clr_column():
        print("Trying Flask method...")
        add_clr_column_via_flask()
