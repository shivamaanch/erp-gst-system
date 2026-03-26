#!/usr/bin/env python3
"""
Simple Database Fix for Live Environment
"""

def create_fix_script():
    """Create database fix script for live deployment"""
    
    fix_content = '''#!/usr/bin/env python3
"""
Database Fix for Live Environment
Adds missing voucher_no columns
"""

import sys
sys.path.insert(0, '/app')

try:
    from app import app
    from extensions import db
    from sqlalchemy import text
    
    with app.app_context():
        print("Starting database fix...")
        
        # Add voucher_no to bills table
        try:
            db.session.execute(text('ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50)'))
            db.session.commit()
            print("Added voucher_no to bills table")
        except Exception as e:
            print(f"bills.voucher_no issue: {e}")
            db.session.rollback()
        
        # Add voucher_no to milk_transactions table
        try:
            db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50)'))
            db.session.commit()
            print("Added voucher_no to milk_transactions table")
        except Exception as e:
            print(f"milk_transactions.voucher_no issue: {e}")
            db.session.rollback()
        
        print("Database fix completed!")
        
except Exception as e:
    print(f"Fix failed: {e}")
    import traceback
    traceback.print_exc()
'''
    
    with open('live_db_fix.py', 'w') as f:
        f.write(fix_content)
    
    print("Created live_db_fix.py")
    return 'live_db_fix.py'

def create_ssh_instructions():
    """Create SSH instructions for Northflank"""
    
    instructions = '''# NORTHFLANK DATABASE FIX INSTRUCTIONS

## PROBLEM
Live database missing voucher_no columns causing build errors.

## SOLUTION
SSH into Northflank container and run database fix.

## STEPS

### 1. SSH into Container
```bash
ssh p01--accts--gzfb6r9tnqwp.code.run
```

### 2. Run Database Fix
```bash
cd /app
python live_db_fix.py
```

### 3. Restart Application (if needed)
```bash
# Application should auto-restart
# If not, restart through Northflank dashboard
```

## EXPECTED OUTPUT
```
Starting database fix...
Added voucher_no to bills table
Added voucher_no to milk_transactions table
Database fix completed!
```

## VERIFICATION
After fix:
- Check Northflank logs
- Application should start without database errors
- Build should complete successfully

## ALTERNATIVE METHOD
If SSH doesn't work:
1. Use Northflank "Shell (SSH)" in dashboard
2. Navigate to /app directory
3. Run the fix script
4. Monitor logs for success

## TROUBLESHOOTING
If fix fails:
- Check database permissions
- Verify PostgreSQL connection
- Check Northflank logs for detailed errors
- Contact support if needed
'''
    
    with open('NORTHLANK_FIX_INSTRUCTIONS.md', 'w') as f:
        f.write(instructions)
    
    print("Created NORTHLANK_FIX_INSTRUCTIONS.md")
    return 'NORTHLANK_FIX_INSTRUCTIONS.md'

def main():
    print("SIMPLE DATABASE FIX FOR LIVE ENVIRONMENT")
    print("Creating fix for voucher_no column issue...")
    
    # Create fix script
    fix_script = create_fix_script()
    
    # Create instructions
    instructions = create_ssh_instructions()
    
    print("\n" + "=" * 50)
    print("DATABASE FIX READY")
    print("=" * 50)
    print(f"Fix script: {fix_script}")
    print(f"Instructions: {instructions}")
    
    print("\nIMMEDIATE ACTION:")
    print("1. Upload live_db_fix.py to Northflank container")
    print("2. SSH into: p01--accts--gzfb6r9tnqwp.code.run")
    print("3. Run: python live_db_fix.py")
    print("4. Monitor build status")
    
    print("\nThis will fix the database column issue and get your build working!")

if __name__ == "__main__":
    main()
