#!/usr/bin/env python3
"""
Migration script to add is_cancelled column to journal_headers table
Run this on your production PostgreSQL database (Neon)
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

def add_is_cancelled_column():
    """Add is_cancelled column to journal_headers table if it doesn't exist"""
    app = create_app()
    with app.app_context():
        try:
            # Check if column exists first
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('journal_headers')]
            
            if 'is_cancelled' not in columns:
                print("🔧 Adding is_cancelled column to journal_headers table...")
                
                # For PostgreSQL
                sql = "ALTER TABLE journal_headers ADD COLUMN is_cancelled BOOLEAN NOT NULL DEFAULT FALSE"
                db.engine.execute(sql)
                db.session.commit()
                
                print("✅ Successfully added is_cancelled column")
            else:
                print("✅ is_cancelled column already exists")
                
        except Exception as e:
            print(f"❌ Error adding column: {e}")
            
            # Try alternative approach
            try:
                print("🔄 Trying alternative approach...")
                sql = "ALTER TABLE journal_headers ADD COLUMN IF NOT EXISTS is_cancelled BOOLEAN DEFAULT FALSE"
                db.engine.execute(sql)
                db.session.commit()
                print("✅ Successfully added is_cancelled column (alternative)")
            except Exception as e2:
                print(f"❌ Alternative failed: {e2}")
                return False
        
        return True

if __name__ == "__main__":
    print("🚀 Running migration to add is_cancelled column...")
    success = add_is_cancelled_column()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("📊 Your Trial Balance and reports should now work properly.")
    else:
        print("\n❌ Migration failed. Please run manually:")
        print("   ALTER TABLE journal_headers ADD COLUMN is_cancelled BOOLEAN NOT NULL DEFAULT FALSE;")
