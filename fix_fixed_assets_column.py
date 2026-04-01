"""
Quick script to add missing fin_year column to fixed_assets table
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

# Add fin_year column if it doesn't exist
if 'fin_year' not in column_names:
    print("Adding fin_year column...")
    cursor.execute("ALTER TABLE fixed_assets ADD COLUMN fin_year VARCHAR(10) DEFAULT '2025-26'")
    conn.commit()
    print("✅ fin_year column added successfully!")
else:
    print("✅ fin_year column already exists")

# Verify the change
cursor.execute("PRAGMA table_info(fixed_assets)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]
print(f"Updated columns: {column_names}")

conn.close()
print("Done!")
