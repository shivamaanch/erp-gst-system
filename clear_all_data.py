#!/usr/bin/env python3
"""
Script to clear all data from the ERP database
"""
import os
from sqlalchemy import create_engine, text

def clear_all_data():
    """Clear all data from all tables"""
    
    # Get database path
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'erp.db')
    
    if not os.path.exists(db_path):
        print("❌ Database file not found")
        return False
    
    print(f"🗑️ Clearing all data from: {db_path}")
    
    try:
        # Create engine
        engine = create_engine(f"sqlite:///{db_path}")
        
        with engine.begin() as conn:
            # Get all table names
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"📋 Found tables: {tables}")
            
            # Clear data from each table (except sqlite_sequence)
            for table in tables:
                if table != 'sqlite_sequence':
                    try:
                        # Get row count before deletion
                        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        row_count = count_result.scalar()
                        
                        if row_count > 0:
                            print(f"🗑️ Deleting {row_count} rows from {table}...")
                            conn.execute(text(f"DELETE FROM {table}"))
                            print(f"✅ Cleared {table}")
                        else:
                            print(f"ℹ️ {table} is already empty")
                    except Exception as e:
                        print(f"⚠️ Could not clear {table}: {e}")
            
            # Reset auto-increment sequences
            print("🔄 Resetting auto-increment sequences...")
            for table in tables:
                if table != 'sqlite_sequence':
                    try:
                        conn.execute(text(f"DELETE FROM sqlite_sequence WHERE name='{table}'"))
                    except Exception:
                        pass  # Ignore if sequence doesn't exist
            
            print("✅ All data cleared successfully!")
            
            # Verify all tables are empty
            print("\n🔍 Verification:")
            for table in tables:
                if table != 'sqlite_sequence':
                    try:
                        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        row_count = count_result.scalar()
                        print(f"📊 {table}: {row_count} rows")
                    except Exception as e:
                        print(f"⚠️ Could not verify {table}: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        return False

if __name__ == "__main__":
    print("⚠️  WARNING: This will delete ALL data from the ERP database!")
    print("📝 This includes:")
    print("   • All companies and users")
    print("   • All financial years")
    print("   • All transactions (milk, journal, bills)")
    print("   • All parties and accounts")
    print("   • All reports and data")
    print("")
    
    confirm = input("🤔 Are you absolutely sure you want to delete ALL data? (type 'DELETE ALL DATA' to confirm): ")
    
    if confirm == "DELETE ALL DATA":
        print("🗑️ Deleting all data...")
        if clear_all_data():
            print("✅ All data has been deleted successfully!")
            print("🔄 You can now start fresh with a clean database.")
        else:
            print("❌ Failed to clear data")
    else:
        print("❌ Operation cancelled - no data was deleted")
