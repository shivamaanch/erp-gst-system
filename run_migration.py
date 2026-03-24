#!/usr/bin/env python3
import sqlite3
import os

# Read the migration script
migration_file = 'database_migration_multi_customer.sql'
db_file = 'instance/erp.db'

if not os.path.exists(migration_file):
    print(f"Migration file {migration_file} not found!")
    exit(1)

if not os.path.exists(db_file):
    print(f"Database file {db_file} not found!")
    exit(1)

# Read migration SQL
with open(migration_file, 'r') as f:
    migration_sql = f.read()

# Connect to database and run migration
try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Split SQL by semicolons and execute each statement
    statements = migration_sql.split(';')
    
    for statement in statements:
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            try:
                cursor.execute(statement)
                print(f"Executed: {statement[:50]}...")
            except sqlite3.Error as e:
                print(f"Error executing: {statement[:50]}... - {e}")
    
    conn.commit()
    conn.close()
    print("Migration completed successfully!")
    
except sqlite3.Error as e:
    print(f"Database error: {e}")
except Exception as e:
    print(f"Error: {e}")
