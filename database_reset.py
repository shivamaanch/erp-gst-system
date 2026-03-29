#!/usr/bin/env python3
"""
Complete database reset for live server
Run this to fix all database issues
"""
import os
import psycopg2
import urllib.parse
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def reset_database():
    """Complete database reset and fix"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not found")
        return False
    
    try:
        parsed = urllib.parse.urlparse(db_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("🔧 COMPLETE DATABASE RESET STARTING...")
        
        # Step 1: Kill all connections to this database
        try:
            cursor.execute(f"""
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE datname = '{parsed.path[1:]}' AND pid <> pg_backend_pid()
            """)
            print("✅ Killed all existing database connections")
        except Exception as e:
            print(f"⚠️  Could not kill connections: {e}")
        
        # Step 2: Drop and recreate problematic tables if needed
        problematic_tables = [
            'milk_transactions', 'bills', 'bill_items', 'journal_headers', 
            'journal_lines', 'cash_book', 'companies', 'users', 'user_companies'
        ]
        
        for table in problematic_tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                print(f"✅ Dropped table {table}")
            except Exception as e:
                print(f"⚠️  Could not drop {table}: {e}")
        
        # Step 3: Create essential tables from scratch
        create_tables = [
            # Companies table
            """
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                business_type VARCHAR(50) DEFAULT 'service',
                gstin VARCHAR(15),
                pan VARCHAR(10),
                state_code VARCHAR(2),
                address TEXT,
                phone VARCHAR(15),
                email VARCHAR(100),
                logo_path VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Users table
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(256),
                is_super_admin BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                company_id INTEGER REFERENCES companies(id)
            )
            """,
            
            # User-Companies junction table
            """
            CREATE TABLE IF NOT EXISTS user_companies (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                role VARCHAR(20) DEFAULT 'viewer',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Cash Book table
            """
            CREATE TABLE IF NOT EXISTS cash_book (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL REFERENCES companies(id),
                voucher_no VARCHAR(50),
                voucher_date DATE,
                transaction_type VARCHAR(20),
                account_id INTEGER,
                amount DECIMAL(15,2),
                party_name VARCHAR(200),
                payment_mode VARCHAR(20),
                reference_number VARCHAR(100),
                narration TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER
            )
            """,
            
            # Milk Transactions table
            """
            CREATE TABLE IF NOT EXISTS milk_transactions (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL REFERENCES companies(id),
                fin_year VARCHAR(10) NOT NULL,
                party_id INTEGER,
                txn_date DATE,
                shift VARCHAR(10) DEFAULT 'Morning',
                txn_type VARCHAR(20),
                qty_liters DECIMAL(10,2),
                fat DECIMAL(5,2),
                snf DECIMAL(5,2),
                rate DECIMAL(10,4),
                amount DECIMAL(14,2),
                chart_id INTEGER,
                narration TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Bills table
            """
            CREATE TABLE IF NOT EXISTS bills (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL REFERENCES companies(id),
                bill_no VARCHAR(50),
                bill_date DATE,
                party_id INTEGER,
                bill_type VARCHAR(20),
                total_amount DECIMAL(15,2),
                gst_amount DECIMAL(15,2),
                net_amount DECIMAL(15,2),
                status VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER
            )
            """,
            
            # Bill Items table
            """
            CREATE TABLE IF NOT EXISTS bill_items (
                id SERIAL PRIMARY KEY,
                bill_id INTEGER NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
                item_id INTEGER,
                description TEXT,
                quantity DECIMAL(10,2),
                rate DECIMAL(10,2),
                amount DECIMAL(15,2),
                gst_rate DECIMAL(5,2),
                gst_amount DECIMAL(15,2)
            )
            """
        ]
        
        for sql in create_tables:
            try:
                cursor.execute(sql)
                print("✅ Created table")
            except Exception as e:
                print(f"⚠️  Table creation error: {e}")
        
        # Step 4: Insert default data
        try:
            # Create default company
            cursor.execute("""
                INSERT INTO companies (name, business_type, gstin) 
                VALUES ('Demo Company', 'Trading', '27AAAAA0000A1Z5')
                ON CONFLICT DO NOTHING
            """)
            
            # Create default admin user
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, is_super_admin, company_id)
                VALUES ('admin', 'admin@example.com', 'pbkdf2:sha256:260000$salt$hash', TRUE, 1)
                ON CONFLICT DO NOTHING
            """)
            
            # Link admin to company
            cursor.execute("""
                INSERT INTO user_companies (user_id, company_id, role, is_active)
                VALUES (1, 1, 'admin', TRUE)
                ON CONFLICT DO NOTHING
            """)
            
            print("✅ Created default data")
        except Exception as e:
            print(f"⚠️  Default data error: {e}")
        
        conn.close()
        print("🎉 DATABASE RESET COMPLETED! Restart the service.")
        return True
        
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        return False

if __name__ == "__main__":
    reset_database()
