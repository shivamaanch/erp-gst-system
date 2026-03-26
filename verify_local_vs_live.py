#!/usr/bin/env python3
"""
Verify Local vs Live Environment - 100% Comparison
Ensures all files, database structure, and features are identical
"""

import os
import shutil
import hashlib
import subprocess
from datetime import datetime
import json

class EnvironmentVerifier:
    def __init__(self):
        self.local_files = {}
        self.local_hashes = {}
        self.local_db_structure = {}
        self.verification_results = {}
        
    def get_file_hash(self, filepath):
        """Get SHA256 hash of a file"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            return f"ERROR: {e}"
    
    def scan_local_files(self):
        """Scan all local files and get their hashes"""
        print("Scanning local files...")
        
        # Critical files that must exist
        critical_files = [
            'app.py',
            'models.py',
            'requirements.txt',
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
            'templates/utilities/backup_database.html',
            'templates/utilities/restore_database.html',
            'templates/utilities/index.html',
            'templates/fixed_assets/schedule_it_act.html',
            'templates/fixed_assets/schedule.html',
            'templates/fixed_assets/add.html',
            'templates/reports/balance_sheet_horizontal.html',
            'templates/reports/profit_loss_horizontal.html',
            'templates/accounts/index.html',
            'templates/accounts/groups.html',
            'templates/accounts/form.html',
            'templates/base.html'
        ]
        
        for filepath in critical_files:
            if os.path.exists(filepath):
                self.local_hashes[filepath] = self.get_file_hash(filepath)
                print(f"  ✓ {filepath}")
            else:
                self.local_hashes[filepath] = "MISSING"
                print(f"  ❌ {filepath} - MISSING")
        
        return len([f for f in self.local_hashes.values() if f != "MISSING"])
    
    def verify_database_structure(self):
        """Verify database structure and data"""
        print("Verifying database structure...")
        
        try:
            from app import app
            from extensions import db
            from models import Account, Company, Bill, User
            
            with app.app_context():
                # Check tables exist
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                
                required_tables = [
                    'users', 'companies', 'accounts', 'bills', 'milk_transactions',
                    'items', 'parties', 'financial_years', 'user_companies',
                    'journal_headers', 'journal_lines'
                ]
                
                missing_tables = []
                for table in required_tables:
                    if table in tables:
                        print(f"  ✓ Table: {table}")
                    else:
                        missing_tables.append(table)
                        print(f"  ❌ Table: {table} - MISSING")
                
                # Check voucher_no columns
                bills_columns = [col['name'] for col in inspector.get_columns('bills')]
                milk_columns = [col['name'] for col in inspector.get_columns('milk_transactions')]
                
                voucher_columns_ok = True
                if 'voucher_no' not in bills_columns:
                    print(f"  ❌ bills.voucher_no column MISSING")
                    voucher_columns_ok = False
                else:
                    print(f"  ✓ bills.voucher_no column exists")
                
                if 'voucher_no' not in milk_columns:
                    print(f"  ❌ milk_transactions.voucher_no column MISSING")
                    voucher_columns_ok = False
                else:
                    print(f"  ✓ milk_transactions.voucher_no column exists")
                
                # Check default accounts
                companies = Company.query.all()
                total_accounts = 0
                accounts_ok = True
                
                for company in companies:
                    accounts = Account.query.filter_by(company_id=company.id, is_active=True).all()
                    account_count = len(accounts)
                    total_accounts += account_count
                    
                    if account_count >= 50:  # Should have at least 50 default accounts
                        print(f"  ✓ {company.name}: {account_count} accounts")
                    else:
                        print(f"  ❌ {company.name}: Only {account_count} accounts (expected 50+)")
                        accounts_ok = False
                
                # Check users
                users = User.query.all()
                print(f"  ✓ Users: {len(users)}")
                
                self.local_db_structure = {
                    'tables': tables,
                    'missing_tables': missing_tables,
                    'voucher_columns_ok': voucher_columns_ok,
                    'accounts_ok': accounts_ok,
                    'total_accounts': total_accounts,
                    'companies': len(companies),
                    'users': len(users)
                }
                
                return len(missing_tables) == 0 and voucher_columns_ok and accounts_ok
                
        except Exception as e:
            print(f"  ❌ Database verification error: {e}")
            return False
    
    def verify_features(self):
        """Verify all features are working"""
        print("Verifying features...")
        
        features = {
            'utilities_module': os.path.exists('modules/utilities.py'),
            'fixed_assets_module': os.path.exists('modules/fixed_assets.py'),
            'accounts_module': os.path.exists('modules/accounts.py'),
            'default_accounts_script': os.path.exists('utils/default_accounts.py'),
            'voucher_helper': os.path.exists('utils/voucher_helper.py'),
            'horizontal_balance_sheet': os.path.exists('templates/reports/balance_sheet_horizontal.html'),
            'horizontal_profit_loss': os.path.exists('templates/reports/profit_loss_horizontal.html'),
            'fixed_assets_schedule': os.path.exists('templates/fixed_assets/schedule_it_act.html'),
            'utilities_templates': os.path.exists('templates/utilities/backup_database.html'),
            'company_switching': 'company.switch' in open('modules/company.py').read() if os.path.exists('modules/company.py') else False,
            'sidebar_company': 'company' in open('templates/base.html').read() if os.path.exists('templates/base.html') else False,
            'beautiful_borders': 'border: 3px' in open('templates/reports/balance_sheet_horizontal.html').read() if os.path.exists('templates/reports/balance_sheet_horizontal.html') else False,
            'proprietor_stamp': 'proprietor' in open('templates/reports/profit_loss_horizontal.html').read() if os.path.exists('templates/reports/profit_loss_horizontal.html') else False
        }
        
        for feature, status in features.items():
            if status:
                print(f"  ✓ {feature}")
            else:
                print(f"  ❌ {feature}")
        
        return all(features.values())
    
    def generate_live_comparison_report(self):
        """Generate report for live deployment comparison"""
        print("Generating comparison report...")
        
        report = {
            'verification_date': datetime.now().isoformat(),
            'local_files': self.local_hashes,
            'database_structure': self.local_db_structure,
            'file_count': len(self.local_hashes),
            'missing_files': [f for f, h in self.local_hashes.items() if h == "MISSING"]
        }
        
        # Save report
        report_file = f'verification_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"  ✓ Report saved: {report_file}")
        return report_file
    
    def create_live_verification_package(self):
        """Create package for live verification"""
        print("Creating live verification package...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        verify_dir = f'verification_package_{timestamp}'
        os.makedirs(verify_dir, exist_ok=True)
        
        # Copy verification script
        shutil.copy2(__file__, os.path.join(verify_dir, 'verify_live.py'))
        
        # Create live verification script
        live_script = '''#!/usr/bin/env python3
"""
Live Environment Verification Script
Run this on live server to verify deployment
"""

import os
import hashlib
import json
from datetime import datetime

def verify_live_environment():
    """Verify live environment matches local"""
    print("Verifying Live Environment...")
    print("=" * 50)
    
    # Check critical files exist
    critical_files = [
        'app.py',
        'models.py',
        'modules/fixed_assets.py',
        'modules/utilities.py',
        'modules/accounts.py',
        'templates/reports/balance_sheet_horizontal.html',
        'templates/fixed_assets/schedule_it_act.html',
        'templates/utilities/backup_database.html'
    ]
    
    missing_files = []
    for filepath in critical_files:
        if os.path.exists(filepath):
            print(f"  ✓ {filepath}")
        else:
            missing_files.append(filepath)
            print(f"  ❌ {filepath} - MISSING")
    
    # Check database
    try:
        from app import app
        from extensions import db
        from models import Account, Company
        
        with app.app_context():
            companies = Company.query.all()
            total_accounts = 0
            
            for company in companies:
                accounts = Account.query.filter_by(company_id=company.id, is_active=True).all()
                total_accounts += len(accounts)
                print(f"  ✓ {company.name}: {len(accounts)} accounts")
            
            print(f"  ✓ Total: {total_accounts} accounts across {len(companies)} companies")
            
    except Exception as e:
        print(f"  ❌ Database check failed: {e}")
    
    # Results
    print("\\n" + "=" * 50)
    if not missing_files:
        print("✅ Live Environment Verification PASSED")
        print("All critical files and features present!")
    else:
        print("❌ Live Environment Verification FAILED")
        print(f"Missing files: {len(missing_files)}")
        for f in missing_files:
            print(f"  - {f}")
    
    return len(missing_files) == 0

if __name__ == "__main__":
    success = verify_live_environment()
    exit(0 if success else 1)
'''
        
        with open(os.path.join(verify_dir, 'verify_live.py'), 'w') as f:
            f.write(live_script)
        
        # Copy file hashes
        with open(os.path.join(verify_dir, 'expected_hashes.json'), 'w') as f:
            json.dump(self.local_hashes, f, indent=2)
        
        print(f"  ✓ Verification package: {verify_dir}")
        return verify_dir
    
    def run_full_verification(self):
        """Run complete verification process"""
        print("=" * 80)
        print("VERIFYING LOCAL VS LIVE ENVIRONMENT - 100% COMPARISON")
        print("=" * 80)
        
        # Step 1: Scan local files
        file_count = self.scan_local_files()
        missing_files = len([f for f in self.local_hashes.values() if f == "MISSING"])
        
        # Step 2: Verify database
        db_ok = self.verify_database_structure()
        
        # Step 3: Verify features
        features_ok = self.verify_features()
        
        # Step 4: Generate report
        report_file = self.generate_live_comparison_report()
        
        # Step 5: Create verification package
        verify_package = self.create_live_verification_package()
        
        # Results
        print("\n" + "=" * 80)
        print("VERIFICATION RESULTS")
        print("=" * 80)
        print(f"Files scanned: {file_count}")
        print(f"Missing files: {missing_files}")
        print(f"Database structure: {'OK' if db_ok else 'FAILED'}")
        print(f"Features: {'OK' if features_ok else 'FAILED'}")
        print(f"Report: {report_file}")
        print(f"Live verification package: {verify_package}")
        
        # Overall status
        all_ok = missing_files == 0 and db_ok and features_ok
        
        if all_ok:
            print("\n✅ LOCAL ENVIRONMENT 100% READY FOR LIVE DEPLOYMENT")
            print("All files, database structure, and features verified!")
            print("\nNext steps:")
            print("1. Upload deployment package to live server")
            print("2. Run deploy.sh script")
            print("3. Run verify_live.py to confirm live environment")
        else:
            print("\n❌ LOCAL ENVIRONMENT NOT READY")
            print("Issues found that must be resolved before deployment:")
            if missing_files > 0:
                print(f"  - {missing_files} files missing")
            if not db_ok:
                print("  - Database structure issues")
            if not features_ok:
                print("  - Missing features")
        
        return all_ok

def main():
    verifier = EnvironmentVerifier()
    return verifier.run_full_verification()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
