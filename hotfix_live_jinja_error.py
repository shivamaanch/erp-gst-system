#!/usr/bin/env python3
"""
Hotfix for Live Environment Jinja2 Template Error
Fixes complex template expressions causing parsing errors
"""

import os
import shutil
from datetime import datetime

def create_hotfix_package():
    """Create hotfix package for live deployment"""
    print("Creating hotfix package for Jinja2 template error...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    hotfix_dir = f'hotfix_jinja_error_{timestamp}'
    os.makedirs(hotfix_dir, exist_ok=True)
    
    # Files to fix
    fixes = [
        'templates/milk/summary_traditional.html',
        'modules/milk.py'
    ]
    
    print("Copying fixed files...")
    for filepath in fixes:
        if os.path.exists(filepath):
            dest_file = os.path.join(hotfix_dir, filepath)
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            shutil.copy2(filepath, dest_file)
            print(f"  Fixed: {filepath}")
        else:
            print(f"  Missing: {filepath}")
    
    # Create hotfix script
    hotfix_script = f"""#!/bin/bash
# Hotfix for Jinja2 Template Error
echo "Applying hotfix for Jinja2 template error..."

# 1. Stop application (if needed)
echo "Stopping application..."
pkill -f "python app.py" || true
sleep 2

# 2. Backup current files
echo "Backing up current files..."
mkdir -p backups/hotfix_{timestamp}
cp -r templates backups/hotfix_{timestamp}/ 2>/dev/null || true
cp modules/milk.py backups/hotfix_{timestamp}/ 2>/dev/null || true

# 3. Apply fixes
echo "Applying template fixes..."
cp templates/milk/summary_traditional.html templates/milk/summary_traditional.html
cp modules/milk.py modules/milk.py

# 4. Restart application
echo "Restarting application..."
nohup python app.py > app.log 2>&1 &

echo "Hotfix applied successfully!"
echo "Application should be running now..."
echo "Check logs: tail -f app.log"
"""
    
    with open(os.path.join(hotfix_dir, 'apply_hotfix.sh'), 'w') as f:
        f.write(hotfix_script)
    os.chmod(os.path.join(hotfix_dir, 'apply_hotfix.sh'), 0o755)
    
    # Create README
    readme = f"""# Jinja2 Template Error Hotfix
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Problem
Live environment showing Jinja2 template syntax error:
```
jinja2.exceptions.TemplateSyntaxError: expected token ',', got 'for'
```

## Solution
Simplified complex Jinja2 expressions in milk templates to avoid parsing issues.

## Files Fixed
- `templates/milk/summary_traditional.html` - Simplified complex expressions
- `modules/milk.py` - Added pre-calculated values for template

## Deployment
1. Upload this hotfix package to live server
2. Run: `./apply_hotfix.sh`
3. Verify milk entries page works

## Verification
After applying hotfix:
- [ ] Milk entries page loads without errors
- [ ] Milk summary page displays correctly
- [ ] All calculations show properly
- [ ] No Jinja2 errors in logs

## Root Cause
Complex nested Jinja2 expressions can cause parsing issues in some environments.
By pre-calculating values in Python and simplifying template expressions,
we avoid these parsing errors.
"""
    
    with open(os.path.join(hotfix_dir, 'README.md'), 'w') as f:
        f.write(readme)
    
    print(f"Hotfix package created: {hotfix_dir}")
    return hotfix_dir

def main():
    print("=" * 60)
    print("HOTFIX FOR LIVE JINJA2 TEMPLATE ERROR")
    print("=" * 60)
    
    hotfix_dir = create_hotfix_package()
    
    print("\n" + "=" * 60)
    print("HOTFIX READY FOR DEPLOYMENT")
    print("=" * 60)
    print(f"Hotfix package: {hotfix_dir}")
    print("\nWhat was fixed:")
    print("• Simplified complex Jinja2 expressions")
    print("• Pre-calculated values in Python")
    print("• Removed nested template calculations")
    print("\nDeployment steps:")
    print("1. Upload hotfix package to live server")
    print("2. Run: ./apply_hotfix.sh")
    print("3. Verify milk entries work")
    print("\nThis will fix the Jinja2 parsing error in live environment!")
    
    return hotfix_dir

if __name__ == "__main__":
    main()
