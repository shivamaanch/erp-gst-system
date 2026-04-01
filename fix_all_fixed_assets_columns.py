"""
Add all missing columns to fixed_assets table to match the model
"""
import os
import sqlite3

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'erp.db')

print(f"Connecting to database: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check current columns
cursor.execute("PRAGMA table_info(fixed_assets)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

print(f"Current columns: {column_names}")

# Define all required columns with their SQL definitions
required_columns = {
    'fin_year': "VARCHAR(10) DEFAULT '2025-26'",
    'description': "TEXT",
    'opening_wdv': "FLOAT DEFAULT 0.0",
    'purchase_cost': "FLOAT DEFAULT 0.0",
    'depreciation_method': "VARCHAR(20) DEFAULT 'WDV'",
    'depreciation_rate': "FLOAT DEFAULT 15.0",
    'depreciation_block': "VARCHAR(50) DEFAULT 'General'",
    'additions': "FLOAT DEFAULT 0.0",
    'sales': "FLOAT DEFAULT 0.0",
    'annual_depreciation': "FLOAT DEFAULT 0.0",
    'closing_wdv': "FLOAT DEFAULT 0.0",
    'is_active': "BOOLEAN DEFAULT 1",
    'created_at': "DATETIME DEFAULT CURRENT_TIMESTAMP",
    'updated_at': "DATETIME DEFAULT CURRENT_TIMESTAMP"
}

# Add missing columns
added_count = 0
for col_name, col_def in required_columns.items():
    if col_name not in column_names:
        print(f"Adding column: {col_name}")
        try:
            cursor.execute(f"ALTER TABLE fixed_assets ADD COLUMN {col_name} {col_def}")
            conn.commit()
            added_count += 1
            print(f"✅ Added {col_name}")
        except Exception as e:
            print(f"⚠️ Error adding {col_name}: {e}")
    else:
        print(f"✓ Column {col_name} already exists")

print(f"\n✅ Added {added_count} new columns")

# Verify the changes
cursor.execute("PRAGMA table_info(fixed_assets)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]
print(f"\nFinal columns ({len(column_names)}): {column_names}")

conn.close()
print("\nDone!")
