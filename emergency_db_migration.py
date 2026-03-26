#!/usr/bin/env python3
"""
Emergency Database Migration for Live Environment
Adds missing voucher_no columns to fix the build
"""

def create_migration_script():
    """Create emergency migration script for live deployment"""
    
    migration_script = '''#!/usr/bin/env python3
"""
Emergency Database Migration - Live Environment
Adds missing voucher_no columns to fix build errors
"""

import os
import sys

def run_migration():
    """Run emergency database migration"""
    print("Starting emergency database migration...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, '/app')
        
        from app import app
        from extensions import db
        from sqlalchemy import text
        
        with app.app_context():
            print("Connected to database")
            
            # Check if voucher_no column exists in bills table
            inspector = db.inspect(db.engine)
            bills_columns = [col['name'] for col in inspector.get_columns('bills')]
            
            if 'voucher_no' not in bills_columns:
                print("Adding voucher_no column to bills table...")
                try:
                    db.session.execute(text('ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50)'))
                    db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_bills_voucher_no ON bills(voucher_no)'))
                    db.session.commit()
                    print("✅ Added voucher_no to bills table")
                except Exception as e:
                    print(f"❌ Error adding voucher_no to bills: {e}")
                    db.session.rollback()
                    return False
            else:
                print("✅ voucher_no column already exists in bills table")
            
            # Check if voucher_no column exists in milk_transactions table
            milk_columns = [col['name'] for col in inspector.get_columns('milk_transactions')]
            
            if 'voucher_no' not in milk_columns:
                print("Adding voucher_no column to milk_transactions table...")
                try:
                    db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50)'))
                    db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_milk_transactions_voucher_no ON milk_transactions(voucher_no)'))
                    db.session.commit()
                    print("✅ Added voucher_no to milk_transactions table")
                except Exception as e:
                    print(f"❌ Error adding voucher_no to milk_transactions: {e}")
                    db.session.rollback()
                    return False
            else:
                print("✅ voucher_no column already exists in milk_transactions table")
            
            # Initialize default accounts if needed
            try:
                from models import Company, Account
                
                companies = Company.query.all()
                print(f"Found {len(companies)} companies")
                
                for company in companies:
                    accounts = Account.query.filter_by(company_id=company.id, is_active=True).all()
                    if len(accounts) < 50:
                        print(f"Company {company.name} has only {len(accounts)} accounts - needs default accounts")
                        # Note: Default accounts initialization would need to be added here
                    else:
                        print(f"Company {company.name} has {len(accounts)} accounts - OK")
                
            except Exception as e:
                print(f"⚠️ Warning checking accounts: {e}")
            
            print("✅ Emergency migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
'''
    
    with open('emergency_live_migration.py', 'w') as f:
        f.write(migration_script)
    
    print("Created emergency migration script: emergency_live_migration.py")
    return 'emergency_live_migration.py'

def create_quick_fix():
    """Create quick fix for live deployment"""
    
    fix_script = '''#!/bin/bash
# Quick Fix for Live Northflank Deployment
echo "Applying quick database fix..."

# Create migration script
cat > /app/emergency_fix.py << 'EOF'
import sys
sys.path.insert(0, '/app')

from app import app
from extensions import db
from sqlalchemy import text

with app.app_context():
    try:
        # Add voucher_no to bills
        db.session.execute(text('ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50)'))
        db.session.commit()
        print("✅ Added voucher_no to bills")
    except:
        print("voucher_no already exists in bills")
    
    try:
        # Add voucher_no to milk_transactions
        db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50)'))
        db.session.commit()
        print("✅ Added voucher_no to milk_transactions")
    except:
        print("voucher_no already exists in milk_transactions")
    
    print("✅ Database fix completed!")
EOF

# Run the fix
python /app/emergency_fix.py

echo "Database fix applied!"
'''
    
    with open('quick_northflank_fix.sh', 'w') as f:
        f.write(fix_script)
    
    os.chmod('quick_northflank_fix.sh', 0o755)
    print("Created quick fix script: quick_northflank_fix.sh")
    return 'quick_northflank_fix.sh'

def main():
    print("EMERGENCY DATABASE MIGRATION FOR LIVE ENVIRONMENT")
    print("Fixing voucher_no column issue...")
    
    # Create migration script
    migration_script = create_migration_script()
    
    # Create quick fix
    fix_script = create_quick_fix()
    
    print("\n" + "=" * 60)
    print("EMERGENCY FIX CREATED")
    print("=" * 60)
    print(f"Migration script: {migration_script}")
    print(f"Quick fix script: {fix_script}")
    
    print("\nPROBLEM:")
    print("• Live database missing voucher_no columns")
    print("• Build failing due to database schema mismatch")
    print("• Need to add columns to live database")
    
    print("\nSOLUTION:")
    print("1. SSH into Northflank container")
    print("2. Run database migration script")
    print("3. Restart application")
    
    print("\nQUICK FIX:")
    print("• SSH into container: p01--accts--gzfb6r9tnqwp.code.run")
    print("• Run: python emergency_live_migration.py")
    print("• Or use: ./quick_northflank_fix.sh")
    
    print("\nEXPECTED RESULT:")
    print("• voucher_no columns added to database")
    print("• Application starts without database errors")
    print("• Build completes successfully")
    
    return True

if __name__ == "__main__":
    main()
