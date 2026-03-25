#!/usr/bin/env python3
"""
PostgreSQL Migration Script for Northflank Deployment
Run this script to update the database schema for multi-customer support
"""

import os
import psycopg2
from psycopg2 import sql
from datetime import datetime

def get_database_url():
    """Get database URL from environment"""
    return os.getenv('DATABASE_URL')

def run_migration():
    """Run the PostgreSQL migration"""
    db_url = get_database_url()
    
    if not db_url:
        print("❌ DATABASE_URL not found in environment variables!")
        return False
    
    try:
        # Parse database URL
        # Expected format: postgresql://username:password@host:port/database
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading /
            user=parsed.username,
            password=parsed.password
        )
        
        cursor = conn.cursor()
        
        print("🔄 Starting PostgreSQL migration...")
        
        # 1. Add is_super_admin column to users table
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS is_super_admin BOOLEAN DEFAULT FALSE
            """)
            print("✅ Added is_super_admin column to users table")
        except Exception as e:
            print(f"⚠️  Error adding is_super_admin column: {e}")
        
        # 2. Create user_companies table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_companies (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                    role VARCHAR(20) DEFAULT 'viewer',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Created user_companies table")
        except Exception as e:
            print(f"⚠️  Error creating user_companies table: {e}")
        
        # 3. Create company_access_log table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_access_log (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                    action VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    user_agent TEXT
                )
            """)
            print("✅ Created company_access_log table")
        except Exception as e:
            print(f"⚠️  Error creating company_access_log table: {e}")
        
        # 4. Create indexes
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_companies_user_id ON user_companies(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_companies_company_id ON user_companies(company_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_companies_active ON user_companies(is_active)")
            print("✅ Created indexes")
        except Exception as e:
            print(f"⚠️  Error creating indexes: {e}")
        
        # 5. Migrate existing user-company relationships
        try:
            cursor.execute("""
                INSERT INTO user_companies (user_id, company_id, role)
                SELECT id, company_id, role 
                FROM users 
                WHERE company_id IS NOT NULL
                ON CONFLICT DO NOTHING
            """)
            print("✅ Migrated existing user-company relationships")
        except Exception as e:
            print(f"⚠️  Error migrating relationships: {e}")
        
        # 6. Update first user to be super admin
        try:
            cursor.execute("""
                UPDATE users 
                SET is_super_admin = TRUE 
                WHERE id = 1
            """)
            print("✅ Updated first user to super admin")
        except Exception as e:
            print(f"⚠️  Error updating super admin: {e}")
        
        # 7. Verify tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('user_companies', 'company_access_log')
        """)
        tables = cursor.fetchall()
        print(f"✅ Verified tables exist: {[t[0] for t in tables]}")
        
        # 8. Verify columns exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'is_super_admin'
        """)
        columns = cursor.fetchall()
        if columns:
            print("✅ Verified is_super_admin column exists")
        else:
            print("❌ is_super_admin column not found")
        
        conn.commit()
        conn.close()
        
        print("🎉 PostgreSQL migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Northflank PostgreSQL Migration")
    print("=" * 50)
    
    success = run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("📋 Next steps:")
        print("1. Restart your Northflank service")
        print("2. Access your application URL")
        print("3. Test the multi-customer features")
    else:
        print("\n❌ Migration failed!")
        print("📋 Please check:")
        print("1. DATABASE_URL environment variable")
        print("2. Database connection")
        print("3. Database permissions")

if __name__ == "__main__":
    main()
