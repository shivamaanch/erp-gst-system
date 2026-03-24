#!/usr/bin/env python3
import sqlite3
import os

# Essential migration for multi-customer system
db_file = 'instance/erp.db'

if not os.path.exists(db_file):
    print(f"Database file {db_file} not found!")
    exit(1)

try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Add is_super_admin column to users table
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE")
        print("Added is_super_admin column to users table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("is_super_admin column already exists")
        else:
            print(f"Error adding is_super_admin column: {e}")
    
    # Create user_companies table
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            company_id INTEGER NOT NULL,
            role VARCHAR(20) DEFAULT 'viewer',
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        )
        """)
        print("Created user_companies table")
    except sqlite3.Error as e:
        print(f"Error creating user_companies table: {e}")
    
    # Create company_access_log table
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_access_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            company_id INTEGER NOT NULL,
            action VARCHAR(50) NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address VARCHAR(45),
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        )
        """)
        print("Created company_access_log table")
    except sqlite3.Error as e:
        print(f"Error creating company_access_log table: {e}")
    
    # Create indexes
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_companies_user_id ON user_companies(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_companies_company_id ON user_companies(company_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_companies_active ON user_companies(is_active)")
        print("Created indexes")
    except sqlite3.Error as e:
        print(f"Error creating indexes: {e}")
    
    # Migrate existing user-company relationships
    try:
        cursor.execute("""
        INSERT INTO user_companies (user_id, company_id, role)
        SELECT id, company_id, role FROM users WHERE company_id IS NOT NULL
        """)
        print("Migrated existing user-company relationships")
    except sqlite3.Error as e:
        print(f"Error migrating relationships: {e}")
    
    # Update first user to be super admin
    try:
        cursor.execute("UPDATE users SET is_super_admin = TRUE WHERE id = 1")
        print("Updated first user to super admin")
    except sqlite3.Error as e:
        print(f"Error updating super admin: {e}")
    
    conn.commit()
    conn.close()
    print("Essential migration completed successfully!")
    
except sqlite3.Error as e:
    print(f"Database error: {e}")
except Exception as e:
    print(f"Error: {e}")
