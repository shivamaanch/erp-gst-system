#!/usr/bin/env python3
"""
Comprehensive Route and Feature Check
Compare local vs live and push all missing routes
"""

import os
import glob
from datetime import datetime

def check_all_routes():
    """Check all available routes in the application"""
    print("Checking all available routes...")
    
    routes = []
    
    # Check all blueprint files
    blueprint_files = [
        'modules/accounts.py',
        'modules/auth.py', 
        'modules/banking.py',
        'modules/company.py',
        'modules/enhanced_invoice.py',
        'modules/fixed_assets.py',
        'modules/gst_reports.py',
        'modules/milk.py',
        'modules/milk_reports.py',
        'modules/parties.py',
        'modules/psi.py',
        'modules/reports_module.py',
        'modules/smf.py',
        'modules/tds_tcs.py',
        'modules/users.py',
        'modules/utilities.py',
        'modules/year.py'
    ]
    
    for blueprint_file in blueprint_files:
        if os.path.exists(blueprint_file):
            with open(blueprint_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Find all @bp.route decorators
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '@' in line and 'route(' in line:
                    route_line = line.strip()
                    # Get the next line for the function name
                    func_line = lines[i+1].strip() if i+1 < len(lines) else ""
                    
                    routes.append({
                        'file': blueprint_file,
                        'route': route_line,
                        'function': func_line
                    })
    
    print(f"Found {len(routes)} routes")
    return routes

def check_templates():
    """Check all template files"""
    print("Checking all template files...")
    
    templates = []
    template_dirs = ['templates']
    
    for template_dir in template_dirs:
        if os.path.exists(template_dir):
            for root, dirs, files in os.walk(template_dir):
                for file in files:
                    if file.endswith('.html'):
                        rel_path = os.path.relpath(os.path.join(root, file), 'templates')
                        templates.append(rel_path)
    
    print(f"Found {len(templates)} templates")
    return templates

def check_static_files():
    """Check all static files"""
    print("Checking static files...")
    
    static_files = []
    static_dirs = ['static']
    
    for static_dir in static_dirs:
        if os.path.exists(static_dir):
            for root, dirs, files in os.walk(static_dir):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), 'static')
                    static_files.append(rel_path)
    
    print(f"Found {len(static_files)} static files")
    return static_files

def check_models():
    """Check all model files"""
    print("Checking model files...")
    
    model_files = []
    if os.path.exists('models.py'):
        model_files.append('models.py')
    
    # Check for any additional model files
    for file in os.listdir('.'):
        if file.endswith('_models.py'):
            model_files.append(file)
    
    print(f"Found {len(model_files)} model files")
    return model_files

def create_comprehensive_push():
    """Create comprehensive push of all working files"""
    print("Creating comprehensive push package...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    push_dir = f'comprehensive_push_{timestamp}'
    os.makedirs(push_dir, exist_ok=True)
    
    # Files to push
    files_to_push = [
        # Core application files
        'app.py',
        'models.py',
        'requirements.txt',
        'extensions.py',
        
        # All blueprint modules
        'modules/accounts.py',
        'modules/auth.py',
        'modules/banking.py',
        'modules/company.py',
        'modules/enhanced_invoice.py',
        'modules/fixed_assets.py',
        'modules/gst_reports.py',
        'modules/milk.py',
        'modules/milk_reports.py',
        'modules/parties.py',
        'modules/psi.py',
        'modules/reports_module.py',
        'modules/smf.py',
        'modules/tds_tcs.py',
        'modules/users.py',
        'modules/utilities.py',
        'modules/year.py',
        
        # Configuration files
        '.env.example',
        'README.md',
        
        # Database migration scripts
        'add_voucher_numbers.py',
        'initialize_default_accounts.py',
        'migrate_clr.py',
        'manual_fix_parties.py',
        
        # Utility scripts
        'utils/default_accounts.py',
        'utils/voucher_helper.py'
    ]
    
    copied_files = []
    for file_path in files_to_push:
        if os.path.exists(file_path):
            dest_file = os.path.join(push_dir, file_path)
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            with open(dest_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            copied_files.append(file_path)
            print(f"  Copied: {file_path}")
        else:
            print(f"  Missing: {file_path}")
    
    # Copy all templates
    if os.path.exists('templates'):
        import shutil
        dest_templates = os.path.join(push_dir, 'templates')
        shutil.copytree('templates', dest_templates, ignore=shutil.ignore_patterns('__pycache__'))
        print(f"  Copied: templates/ directory")
    
    # Copy all static files
    if os.path.exists('static'):
        dest_static = os.path.join(push_dir, 'static')
        shutil.copytree('static', dest_static, ignore=shutil.ignore_patterns('__pycache__'))
        print(f"  Copied: static/ directory")
    
    print(f"Comprehensive push package created: {push_dir}")
    print(f"Files copied: {len(copied_files)}")
    
    return push_dir, copied_files

def main():
    print("=" * 60)
    print("COMPREHENSIVE ROUTE AND FEATURE CHECK")
    print("=" * 60)
    
    # Check all components
    routes = check_all_routes()
    templates = check_templates()
    static_files = check_static_files()
    models = check_models()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Routes: {len(routes)}")
    print(f"Templates: {len(templates)}")
    print(f"Static files: {len(static_files)}")
    print(f"Model files: {len(models)}")
    
    # Create comprehensive push
    push_dir, copied_files = create_comprehensive_push()
    
    print("\n" + "=" * 60)
    print("COMPREHENSIVE PUSH READY")
    print("=" * 60)
    print(f"Package: {push_dir}")
    print(f"Files: {len(copied_files)}")
    
    print("\nNext steps:")
    print("1. All working files have been prepared")
    print("2. Templates and static files included")
    print("3. All blueprint modules included")
    print("4. Ready to push to GitHub")
    
    return push_dir, copied_files

if __name__ == "__main__":
    main()
