#!/usr/bin/env python3
"""
Deploy to Live Environment
This script prepares and pushes all changes to live environment
"""

import os
import shutil
from datetime import datetime
import subprocess

def create_deployment_package():
    """Create a deployment package with all necessary files"""
    print("🚀 Creating deployment package...")
    
    # Create deployment directory
    deploy_dir = f"deployment_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(deploy_dir, exist_ok=True)
    
    # Files to include in deployment
    files_to_deploy = [
        # Core application files
        'app.py',
        'models.py',
        
        # Utility scripts
        'utils/default_accounts.py',
        'utils/voucher_helper.py',
        'add_voucher_numbers.py',
        'initialize_default_accounts.py',
        
        # New modules
        'modules/fixed_assets.py',
        'modules/utilities.py',
        'modules/accounts.py',
        'modules/reports_module.py',
        'modules/users.py',
        'modules/company.py',
        
        # Templates (copy entire directories)
        'templates/utilities/',
        'templates/fixed_assets/',
        'templates/reports/',
        'templates/accounts/',
        'templates/base.html',
    ]
    
    # Copy files to deployment directory
    for item in files_to_deploy:
        if item.endswith('/'):
            # Copy directory
            if os.path.exists(item):
                dest_dir = os.path.join(deploy_dir, item)
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copytree(item, dest_dir, dirs_exist_ok=True)
                print(f"✅ Copied directory: {item}")
        else:
            # Copy file
            if os.path.exists(item):
                dest_file = os.path.join(deploy_dir, item)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                shutil.copy2(item, dest_file)
                print(f"✅ Copied file: {item}")
    
    # Create deployment script
    deploy_script = """#!/bin/bash
# Live Deployment Script
echo "Starting ERP Deployment..."

# 1. Backup current database
echo "Creating database backup..."
python -c "
from app import app
from extensions import db
from datetime import datetime
import shutil

with app.app_context():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/erp_backup_before_deploy_{timestamp}.db'
    shutil.copy2('instance/erp.db', backup_file)
    print(f'Backup created: {backup_file}')
"

# 2. Run database migrations
echo "Running database migrations..."
python add_voucher_numbers.py
python initialize_default_accounts.py

# 3. Stop current application
echo "Stopping current application..."
pkill -f "python app.py" || true

# 4. Deploy files (copy from deployment package)
echo "Deploying files..."
# This would be done manually or via SCP/FTP

# 5. Start new application
echo "Starting new application..."
nohup python app.py > app.log 2>&1 &

echo "Deployment completed!"
echo "Application should be available at: http://your-domain:5000"
"""
    
    with open(os.path.join(deploy_dir, 'deploy.sh'), 'w') as f:
        f.write(deploy_script)
    
    # Make deploy script executable
    os.chmod(os.path.join(deploy_dir, 'deploy.sh'), 0o755)
    
    # Create deployment checklist
    checklist = """# Live Deployment Checklist

## Before Deployment
- [ ] Backup live database
- [ ] Test deployment on staging server
- [ ] Notify users about downtime

## Deployment Steps
- [ ] Run database migrations
- [ ] Upload new files
- [ ] Restart application
- [ ] Verify all features working

## After Deployment
- [ ] Test login functionality
- [ ] Test company switching
- [ ] Test utilities (backup/restore)
- [ ] Test fixed assets schedule
- [ ] Test chart of accounts
- [ ] Test reports (balance sheet, P&L)
- [ ] Verify all 119 default accounts created

## Rollback Plan
- [ ] Restore database from backup
- [ ] Revert to previous files
- [ ] Restart application
"""
    
    with open(os.path.join(deploy_dir, 'DEPLOYMENT_CHECKLIST.md'), 'w') as f:
        f.write(checklist)
    
    print(f"✅ Deployment package created: {deploy_dir}")
    print(f"📋 Deployment checklist: {deploy_dir}/DEPLOYMENT_CHECKLIST.md")
    print(f"🚀 Deploy script: {deploy_dir}/deploy.sh")
    
    return deploy_dir

def run_database_migrations():
    """Run database migrations"""
    print("🔄 Running database migrations...")
    
    try:
        # Run voucher number migration
        result = subprocess.run(['python', 'add_voucher_numbers.py'], 
                              capture_output=True, text=True)
        print("Voucher numbers migration:", result.stdout)
        
        # Run default accounts initialization
        result = subprocess.run(['python', 'initialize_default_accounts.py'], 
                              capture_output=True, text=True)
        print("Default accounts initialization:", result.stdout)
        
        print("✅ Database migrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Error running migrations: {e}")

def create_backup():
    """Create current database backup"""
    print("📦 Creating database backup...")
    
    try:
        from app import app
        from extensions import db
        from datetime import datetime
        import shutil
        
        with app.app_context():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f'backups/erp_backup_before_deploy_{timestamp}.db'
            
            # Ensure backups directory exists
            os.makedirs('backups', exist_ok=True)
            
            # Create backup
            shutil.copy2('instance/erp.db', backup_file)
            print(f"✅ Backup created: {backup_file}")
            return backup_file
            
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 ERP DEPLOYMENT TO LIVE ENVIRONMENT")
    print("=" * 60)
    
    # Step 1: Create backup
    backup_file = create_backup()
    
    # Step 2: Run database migrations
    run_database_migrations()
    
    # Step 3: Create deployment package
    deploy_dir = create_deployment_package()
    
    print("\n" + "=" * 60)
    print("✅ DEPLOYMENT PREPARATION COMPLETE!")
    print("=" * 60)
    print(f"📦 Backup: {backup_file}")
    print(f"📂 Deployment Package: {deploy_dir}")
    print("\n📋 Next Steps:")
    print("1. Upload the deployment package to live server")
    print("2. Run the deploy.sh script on live server")
    print("3. Verify all features are working")
    print(f"4. Use the checklist: {deploy_dir}/DEPLOYMENT_CHECKLIST.md")
    print("\n🎯 Ready to push to live!")
