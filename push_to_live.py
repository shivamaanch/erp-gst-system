#!/usr/bin/env python3
"""
Push All Changes to Live Environment
Complete deployment script for ERP system
"""

import os
import shutil
import subprocess
from datetime import datetime
import sys

def create_complete_backup():
    """Create complete backup before deployment"""
    print("📦 Creating complete backup...")
    
    try:
        from app import app
        from extensions import db
        import json
        
        with app.app_context():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create backup directory
            backup_dir = f'backups/complete_backup_{timestamp}'
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup database
            db_backup = os.path.join(backup_dir, 'erp.db')
            shutil.copy2('instance/erp.db', db_backup)
            print(f"✅ Database backed up: {db_backup}")
            
            # Backup configuration
            if os.path.exists('.env'):
                shutil.copy2('.env', os.path.join(backup_dir, '.env'))
                print("✅ Configuration backed up")
            
            # Create backup manifest
            manifest = {
                'timestamp': timestamp,
                'database_backup': 'erp.db',
                'version': '1.0',
                'features': [
                    'Utilities System (Backup/Restore/Reindex/Renumber)',
                    'Fixed Assets Schedule (Income Tax Act)',
                    'Horizontal Financial Reports',
                    'Default Chart of Accounts (119 accounts)',
                    'Company Switching',
                    'Beautiful UI with borders'
                ]
            }
            
            with open(os.path.join(backup_dir, 'manifest.json'), 'w') as f:
                json.dump(manifest, f, indent=2)
            
            print(f"✅ Complete backup created: {backup_dir}")
            return backup_dir
            
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return None

def run_all_migrations():
    """Run all database migrations"""
    print("🔄 Running all database migrations...")
    
    migrations = [
        ('Voucher Numbers', 'add_voucher_numbers.py'),
        ('Default Accounts', 'initialize_default_accounts.py')
    ]
    
    for name, script in migrations:
        try:
            print(f"  Running {name} migration...")
            result = subprocess.run(['python', script], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f"  ✅ {name} migration completed")
            else:
                print(f"  ❌ {name} migration failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print(f"  ❌ {name} migration timed out")
            return False
        except Exception as e:
            print(f"  ❌ {name} migration error: {e}")
            return False
    
    print("✅ All migrations completed successfully!")
    return True

def create_production_package():
    """Create production deployment package"""
    print("📦 Creating production deployment package...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    package_dir = f'production_package_{timestamp}'
    os.makedirs(package_dir, exist_ok=True)
    
    # Essential files for production
    production_files = [
        # Core application
        'app.py',
        'models.py',
        'requirements.txt',
        '.env.example',
        
        # New modules
        'modules/fixed_assets.py',
        'modules/utilities.py',
        'modules/accounts.py',
        'modules/reports_module.py',
        'modules/users.py',
        'modules/company.py',
        
        # Utilities and helpers
        'utils/default_accounts.py',
        'utils/voucher_helper.py',
        'add_voucher_numbers.py',
        'initialize_default_accounts.py',
        
        # Templates (copy entire directories)
        'templates/utilities/',
        'templates/fixed_assets/',
        'templates/reports/',
        'templates/accounts/',
        'templates/base.html',
    ]
    
    print("  Copying production files...")
    for item in production_files:
        if item.endswith('/'):
            if os.path.exists(item):
                dest_dir = os.path.join(package_dir, item)
                shutil.copytree(item, dest_dir, dirs_exist_ok=True)
                print(f"    ✅ Copied directory: {item}")
        else:
            if os.path.exists(item):
                dest_file = os.path.join(package_dir, item)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                shutil.copy2(item, dest_file)
                print(f"    ✅ Copied file: {item}")
    
    # Create production deployment script
    deploy_script = f"""#!/bin/bash
# Production Deployment Script
echo "Starting Production Deployment..."

# Set production environment
export FLASK_ENV=production

# 1. Stop current application
echo "⏹️ Stopping current application..."
pkill -f "python app.py" || true
sleep 2

# 2. Backup current database
echo "📦 Creating production backup..."
python -c "
from app import app
from extensions import db
from datetime import datetime
import shutil

with app.app_context():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/production_backup_{{timestamp}}.db'
    os.makedirs('backups', exist_ok=True)
    shutil.copy2('instance/erp.db', backup_file)
    print(f'✅ Production backup: {{backup_file}}')
"

# 3. Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# 4. Run database migrations
echo "🔄 Running database migrations..."
python add_voucher_numbers.py
python initialize_default_accounts.py

# 5. Start production application
echo "▶️ Starting production application..."
nohup python app.py > production.log 2>&1 &

echo "✅ Production deployment completed!"
echo "🌐 Application running at: http://your-domain:5000"
echo "📋 Logs: production.log"
"""
    
    with open(os.path.join(package_dir, 'deploy_production.sh'), 'w') as f:
        f.write(deploy_script)
    os.chmod(os.path.join(package_dir, 'deploy_production.sh'), 0o755)
    
    # Create production README
    readme = f"""# ERP Production Deployment Package

## Deployment Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Features Included:
- ✅ Complete Utilities System (Backup/Restore/Reindex/Renumber/Fix Data)
- ✅ Fixed Assets Schedule (Income Tax Act compliant)
- ✅ Horizontal Financial Reports with beautiful borders
- ✅ Default Chart of Accounts (119 accounts per company)
- ✅ Company Switching with sidebar display
- ✅ Professional UI with thick/slim borders
- ✅ Clickable ledgers in reports
- ✅ PDF/Excel download buttons
- ✅ Print preview optimization

## Deployment Steps:

1. **Upload this entire package to live server**
2. **Run deployment script:**
   ```bash
   chmod +x deploy_production.sh
   ./deploy_production.sh
   ```

3. **Verify deployment:**
   - Login works
   - Company switching works
   - Chart of Accounts shows 119 accounts
   - Fixed Assets Schedule accessible
   - All utilities functional
   - Reports display correctly

## Database Migrations:
- Voucher number system (SV/PV/MV/JV format)
- Default accounts creation
- All migrations run automatically

## Support:
Check production.log for any issues
"""
    
    with open(os.path.join(package_dir, 'README.md'), 'w') as f:
        f.write(readme)
    
    print(f"✅ Production package created: {package_dir}")
    return package_dir

def verify_deployment_readiness():
    """Verify system is ready for deployment"""
    print("🔍 Verifying deployment readiness...")
    
    checks = [
        ("Database exists", lambda: os.path.exists('instance/erp.db')),
        ("App file exists", lambda: os.path.exists('app.py')),
        ("Models file exists", lambda: os.path.exists('models.py')),
        ("Fixed assets module exists", lambda: os.path.exists('modules/fixed_assets.py')),
        ("Utilities module exists", lambda: os.path.exists('modules/utilities.py')),
        ("Default accounts script exists", lambda: os.path.exists('utils/default_accounts.py')),
        ("Voucher helper exists", lambda: os.path.exists('utils/voucher_helper.py')),
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        try:
            if check_func():
                print(f"  ✅ {check_name}")
            else:
                print(f"  ❌ {check_name}")
                all_passed = False
        except Exception as e:
            print(f"  ❌ {check_name}: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Main deployment function"""
    print("=" * 80)
    print("🚀 PUSHING ALL CHANGES TO LIVE ENVIRONMENT")
    print("=" * 80)
    
    # Step 1: Verify readiness
    if not verify_deployment_readiness():
        print("❌ System not ready for deployment!")
        return False
    
    # Step 2: Create backup
    backup_dir = create_complete_backup()
    if not backup_dir:
        print("❌ Failed to create backup!")
        return False
    
    # Step 3: Run migrations
    if not run_all_migrations():
        print("❌ Failed to run migrations!")
        return False
    
    # Step 4: Create production package
    package_dir = create_production_package()
    if not package_dir:
        print("❌ Failed to create production package!")
        return False
    
    print("\n" + "=" * 80)
    print("✅ PUSH TO LIVE PREPARATION COMPLETE!")
    print("=" * 80)
    print(f"📦 Backup: {backup_dir}")
    print(f"📦 Production Package: {package_dir}")
    print("\n🎯 NEXT STEPS:")
    print("1. Upload the production package to your live server")
    print("2. Run: ./deploy_production.sh")
    print("3. Verify all features are working")
    print("\n📋 Features being deployed:")
    print("  • Complete Utilities System")
    print("  • Fixed Assets Schedule (IT Act)")
    print("  • Horizontal Financial Reports")
    print("  • 119 Default Accounts")
    print("  • Company Switching")
    print("  • Beautiful UI with borders")
    print("  • All new templates and modules")
    print("\n🚀 READY TO PUSH TO LIVE!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
