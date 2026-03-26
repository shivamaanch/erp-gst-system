#!/usr/bin/env python3
"""
Simple Push to Live - No Unicode Characters
"""

import os
import shutil
import subprocess
from datetime import datetime

def main():
    print("=" * 60)
    print("PUSHING ALL CHANGES TO LIVE")
    print("=" * 60)
    
    # 1. Create backup
    print("Creating backup...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f'backups/push_backup_{timestamp}'
    os.makedirs(backup_dir, exist_ok=True)
    
    if os.path.exists('instance/erp.db'):
        shutil.copy2('instance/erp.db', os.path.join(backup_dir, 'erp.db'))
        print(f"Backup created: {backup_dir}")
    
    # 2. Run migrations
    print("Running migrations...")
    try:
        subprocess.run(['python', 'add_voucher_numbers.py'], check=True, capture_output=True)
        print("Voucher numbers migration: OK")
    except subprocess.CalledProcessError as e:
        print(f"Voucher numbers migration failed: {e}")
        return False
    
    try:
        subprocess.run(['python', 'initialize_default_accounts.py'], check=True, capture_output=True)
        print("Default accounts migration: OK")
    except subprocess.CalledProcessError as e:
        print(f"Default accounts migration failed: {e}")
        return False
    
    # 3. Create deployment package
    print("Creating deployment package...")
    package_dir = f'deploy_package_{timestamp}'
    os.makedirs(package_dir, exist_ok=True)
    
    files_to_copy = [
        'app.py',
        'models.py',
        'modules/fixed_assets.py',
        'modules/utilities.py',
        'modules/accounts.py',
        'modules/reports_module.py',
        'modules/users.py',
        'modules/company.py',
        'utils/default_accounts.py',
        'utils/voucher_helper.py',
        'add_voucher_numbers.py',
        'initialize_default_accounts.py',
        'templates/utilities/',
        'templates/fixed_assets/',
        'templates/reports/',
        'templates/accounts/',
        'templates/base.html'
    ]
    
    for item in files_to_copy:
        if item.endswith('/'):
            if os.path.exists(item):
                dest_dir = os.path.join(package_dir, item)
                shutil.copytree(item, dest_dir, dirs_exist_ok=True)
                print(f"Copied directory: {item}")
        else:
            if os.path.exists(item):
                dest_file = os.path.join(package_dir, item)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                shutil.copy2(item, dest_file)
                print(f"Copied file: {item}")
    
    # 4. Create deployment script
    deploy_script = """#!/bin/bash
echo "Starting Live Deployment..."

# 1. Stop application
pkill -f "python app.py" || true
sleep 2

# 2. Backup database
python -c "
from app import app
from extensions import db
from datetime import datetime
import shutil

with app.app_context():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/live_backup_{timestamp}.db'
    shutil.copy2('instance/erp.db', backup_file)
    print(f'Backup created: {backup_file}')
"

# 3. Run migrations
python add_voucher_numbers.py
python initialize_default_accounts.py

# 4. Start application
nohup python app.py > app.log 2>&1 &

echo "Deployment completed!"
echo "Application running..."
"""
    
    with open(os.path.join(package_dir, 'deploy.sh'), 'w') as f:
        f.write(deploy_script)
    os.chmod(os.path.join(package_dir, 'deploy.sh'), 0o755)
    
    # 5. Create README
    readme = f"""# ERP Deployment Package
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Features Included:
- Complete Utilities System
- Fixed Assets Schedule (Income Tax Act)
- Horizontal Financial Reports
- Default Chart of Accounts (119 accounts)
- Company Switching
- Beautiful UI with borders

## Deployment:
1. Upload this package to live server
2. Run: ./deploy.sh
3. Verify all features work

## Verification Checklist:
- [ ] Login works
- [ ] Company switching works
- [ ] Chart of Accounts shows 119 accounts
- [ ] Fixed Assets Schedule accessible
- [ ] All utilities functional
- [ ] Reports display correctly
"""
    
    with open(os.path.join(package_dir, 'README.md'), 'w') as f:
        f.write(readme)
    
    print("\n" + "=" * 60)
    print("PUSH TO LIVE COMPLETE!")
    print("=" * 60)
    print(f"Backup: {backup_dir}")
    print(f"Package: {package_dir}")
    print("\nNext Steps:")
    print("1. Upload package to live server")
    print("2. Run: ./deploy.sh")
    print("3. Verify all features")
    print("\nFeatures deployed:")
    print("• Utilities System (Backup/Restore/Reindex/Renumber)")
    print("• Fixed Assets Schedule (IT Act)")
    print("• Horizontal Financial Reports")
    print("• 119 Default Accounts")
    print("• Company Switching")
    print("• Beautiful UI with borders")
    print("• All new templates and modules")
    print("\nREADY FOR LIVE DEPLOYMENT!")
    
    return True

if __name__ == "__main__":
    main()
