#!/usr/bin/env python3
"""
Fix user company access for live PostgreSQL database
Ensures admin user (ID 1) has access to all companies
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment variables")
    sys.exit(1)

print(f"Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")

try:
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all companies
        result = conn.execute(text("SELECT id, name FROM companies ORDER BY id"))
        companies = result.fetchall()
        
        if not companies:
            print("❌ No companies found in database")
            sys.exit(1)
        
        print(f"📋 Found {len(companies)} companies:")
        for company in companies:
            print(f"   - {company.id}: {company.name}")
        
        # Check existing user_companies for admin user (ID 1)
        result = conn.execute(text("SELECT company_id FROM user_companies WHERE user_id = 1"))
        existing_access = {row.company_id for row in result}
        
        print(f"\n🔍 Admin user currently has access to companies: {existing_access}")
        
        # Add missing access entries
        added_count = 0
        for company in companies:
            if company.id not in existing_access:
                print(f"➕ Adding access to company {company.id}: {company.name}")
                conn.execute(text("""
                    INSERT INTO user_companies (user_id, company_id, role, is_active, created_at)
                    VALUES (1, :company_id, 'admin', 1, NOW())
                """), {"company_id": company.id})
                added_count += 1
        
        if added_count > 0:
            conn.commit()
            print(f"✅ Added access to {added_count} companies")
        else:
            print("✅ Admin user already has access to all companies")
        
        # Verify the fix
        result = conn.execute(text("""
            SELECT c.id, c.name, uc.role 
            FROM companies c
            LEFT JOIN user_companies uc ON c.id = uc.company_id AND uc.user_id = 1
            ORDER BY c.id
        """))
        
        print(f"\n🎯 Final access list:")
        for row in result:
            status = "✅" if row.role else "❌"
            print(f"   {status} {row.id}: {row.name} - {row.role or 'No access'}")
            
except Exception as e:
    print(f"❌ Fix failed: {e}")
    sys.exit(1)

print("\n🎉 User access fix completed!")
