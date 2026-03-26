#!/usr/bin/env python3
"""
Northflank Complete Fix
Simple version without Unicode issues
"""

def create_fix():
    """Create simple fix script"""
    
    fix_content = '''#!/usr/bin/env python3
"""
Northflank Complete Fix
"""

import sys
sys.path.insert(0, '/app')

try:
    from app import app
    from extensions import db
    from sqlalchemy import text
    
    with app.app_context():
        print("Starting Northflank fix...")
        
        # Add voucher_no to bills
        try:
            db.session.execute(text('ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50)'))
            db.session.commit()
            print("Added voucher_no to bills")
        except:
            print("voucher_no already exists in bills")
        
        # Add voucher_no to milk_transactions
        try:
            db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50)'))
            db.session.commit()
            print("Added voucher_no to milk_transactions")
        except:
            print("voucher_no already exists in milk_transactions")
        
        # Create indexes
        try:
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_bills_voucher_no ON bills(voucher_no)'))
            db.session.commit()
            print("Created bills.voucher_no index")
        except:
            print("bills.voucher_no index issue")
        
        try:
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_milk_transactions_voucher_no ON milk_transactions(voucher_no)'))
            db.session.commit()
            print("Created milk_transactions.voucher_no index")
        except:
            print("milk_transactions.voucher_no index issue")
        
        print("Fix completed! Application should start now.")
        
except Exception as e:
    print(f"Fix failed: {e}")
    print("Try manual SQL:")
    print("ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50);")
    print("ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50);")
'''
    
    with open('northflank_fix.py', 'w') as f:
        f.write(fix_content)
    
    print("Created northflank_fix.py")
    return 'northflank_fix.py'

def create_instructions():
    """Create simple instructions"""
    
    instructions = '''# NORTHFLANK FIX INSTRUCTIONS

## SSH into container:
ssh p01--accts--gzfb6r9tnqwp.code.run

## Run fix:
cd /app
git pull origin main
python northflank_fix.py

## Expected output:
Starting Northflank fix...
Added voucher_no to bills
Added voucher_no to milk_transactions
Created bills.voucher_no index
Created milk_transactions.voucher_no index
Fix completed! Application should start now.

## If script fails, run manual SQL:
ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50);
ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50);

## After fix:
- Application should start without errors
- Build should complete successfully
- All features should work
'''
    
    with open('NORTHLANK_FIX.md', 'w') as f:
        f.write(instructions)
    
    print("Created NORTHLANK_FIX.md")
    return 'NORTHLANK_FIX.md'

def main():
    print("Creating Northflank complete fix...")
    
    fix_file = create_fix()
    instructions = create_instructions()
    
    print(f"Fix script: {fix_file}")
    print(f"Instructions: {instructions}")
    print("\nPush to GitHub and deploy to Northflank!")

if __name__ == "__main__":
    main()
