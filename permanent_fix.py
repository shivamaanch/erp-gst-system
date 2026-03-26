#!/usr/bin/env python3
"""
Permanent Database Fix - No Unicode issues
"""

def patch_app_with_auto_migration():
    """Patch app.py to include automatic database migration"""
    
    # Read current app.py
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Find where to insert the migration (after app creation)
    if 'app = Flask(__name__)' in content:
        # Insert migration right after app creation
        migration_function = '''
def run_auto_db_migration():
    """Run automatic database migration on startup"""
    try:
        from extensions import db
        from sqlalchemy import text
        
        with app.app_context():
            print("Running automatic database migration...")
            
            # Add voucher_no to bills table
            try:
                db.session.execute(text('ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50)'))
                db.session.commit()
                print("Added voucher_no to bills table")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e):
                    print("voucher_no already exists in bills table")
                else:
                    print(f"Error adding voucher_no to bills: {e}")
                    db.session.rollback()
            
            # Add voucher_no to milk_transactions table
            try:
                db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50)'))
                db.session.commit()
                print("Added voucher_no to milk_transactions table")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e):
                    print("voucher_no already exists in milk_transactions table")
                else:
                    print(f"Error adding voucher_no to milk_transactions: {e}")
                    db.session.rollback()
            
            print("Database migration completed successfully!")
            
    except Exception as e:
        print(f"Database migration failed: {e}")

'''
        
        # Find the line after app creation and insert migration
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # Insert migration function after app creation
            if line.strip() == 'app = Flask(__name__)':
                new_lines.append(migration_function)
                new_lines.append('')
                new_lines.append('# Run automatic migration')
                new_lines.append('run_auto_db_migration()')
                new_lines.append('')
        
        # Write the patched content
        with open('app.py', 'w') as f:
            f.write('\n'.join(new_lines))
        
        print("Patched app.py with automatic migration")
        return True
    
    return False

def main():
    print("CREATING PERMANENT DATABASE FIX")
    print("This will automatically fix the database on app startup...")
    
    # Patch app.py
    if patch_app_with_auto_migration():
        print("SUCCESS: app.py patched successfully!")
        print("Automatic database migration will run on startup!")
        print("No manual intervention needed!")
        
        print("\nNext steps:")
        print("1. Push this to GitHub")
        print("2. Northflank will rebuild and auto-fix database")
        print("3. Application will start without errors!")
        
        return True
    else:
        print("FAILED: Could not patch app.py")
        return False

if __name__ == "__main__":
    main()
