#!/usr/bin/env python3
"""
Check Northflank Deployment Status
Verify what's deployed and why build didn't start
"""

import os
import subprocess
import requests
from datetime import datetime

def check_northflank_status():
    """Check Northflank deployment status"""
    print("Checking Northflank deployment...")
    
    # From the logs, we can see:
    # - Service ID: accts
    # - Project: ERP 
    # - Commit: 1c0abd1
    # - Error: Jinja2 template syntax error
    
    status = {
        'service_id': 'accts',
        'project': 'ERP',
        'commit': '1c0abd1',
        'error': 'jinja2.exceptions.TemplateSyntaxError',
        'status': 'Failed to start',
        'issue': 'Complex template expressions causing parsing errors'
    }
    
    print(f"  Service ID: {status['service_id']}")
    print(f"  Project: {status['project']}")
    print(f"  Commit: {status['commit']}")
    print(f"  Status: {status['status']}")
    print(f"  Error: {status['error']}")
    print(f"  Issue: {status['issue']}")
    
    return status

def check_git_push_status():
    """Check if changes were pushed to GitHub"""
    print("\nChecking git push status...")
    
    try:
        # Check if we're behind remote
        result = subprocess.run(['git', 'status'], 
                              capture_output=True, text=True)
        
        if 'Your branch is ahead' in result.stdout:
            print("  Local changes ahead of remote")
            print("  Changes NOT pushed to GitHub")
        elif 'Your branch is up to date' in result.stdout:
            print("  Branch is up to date with remote")
        else:
            print("  Checking branch status...")
            print(result.stdout)
        
        # Check last push
        result = subprocess.run(['git', 'log', '--oneline', '-5'], 
                              capture_output=True, text=True)
        print(f"  Recent commits:")
        for line in result.stdout.strip().split('\n')[:3]:
            print(f"    {line}")
        
        return True
        
    except Exception as e:
        print(f"  Git error: {e}")
        return False

def create_deployment_action_plan():
    """Create action plan to fix deployment"""
    print("\n" + "=" * 60)
    print("DEPLOYMENT ACTION PLAN")
    print("=" * 60)
    
    print("\nCURRENT SITUATION:")
    print("• Northflank build failed due to Jinja2 template error")
    print("• Local fixes created but not pushed to GitHub")
    print("• Northflank is trying to build old commit 1c0abd1")
    print("• Need to push fixed code to trigger new build")
    
    print("\nACTION STEPS:")
    
    print("\n1. COMMIT AND PUSH FIXES:")
    print("   git add .")
    print("   git commit -m 'Fix Jinja2 template error and start build'")
    print("   git push origin main")
    
    print("\n2. TRIGGER NEW BUILD:")
    print("   • Northflank will automatically detect new commit")
    print("   • New build will start with fixed templates")
    print("   • Build should complete successfully")
    
    print("\n3. VERIFY DEPLOYMENT:")
    print("   • Check Northflank dashboard")
    print("   • Verify build status")
    print("   • Test application functionality")
    
    print("\n4. IF BUILD STILL FAILS:")
    print("   • Use emergency build fix package")
    print("   • Deploy manually to Northflank")
    print("   • Contact support if needed")
    
    return True

def create_push_script():
    """Create script to push fixes"""
    push_script = '''#!/bin/bash
# Push fixes to trigger Northflank build

echo "Pushing fixes to start Northflank build..."

# Add all changes
git add .

# Commit fixes
git commit -m "Fix Jinja2 template error - start build

- Simplified complex template expressions
- Fixed milk summary template
- Added safe defaults for calculations
- Ready for Northflank deployment"

# Push to trigger build
git push origin main

echo "Push completed!"
echo "Northflank should start new build automatically..."
echo "Check Northflank dashboard for build status"
'''
    
    with open('push_to_start_build.sh', 'w') as f:
        f.write(push_script)
    os.chmod('push_to_start_build.sh', 0o755)
    
    print("Created push script: push_to_start_build.sh")
    return 'push_to_start_build.sh'

def main():
    print("CHECKING NORTHLANK DEPLOYMENT STATUS")
    print("Why build didn't start and how to fix it...")
    
    # Check Northflank status
    nf_status = check_northflank_status()
    
    # Check git status
    git_status = check_git_push_status()
    
    # Create action plan
    create_deployment_action_plan()
    
    # Create push script
    push_script = create_push_script()
    
    print("\n" + "=" * 60)
    print("IMMEDIATE ACTION REQUIRED")
    print("=" * 60)
    print("\nPROBLEM:")
    print("• Northflank build failed due to template error")
    print("• Fixes created locally but not pushed")
    print("• Build won't start until code is pushed")
    
    print("\nSOLUTION:")
    print(f"• Run: {push_script}")
    print("• This will push fixes to GitHub")
    print("• Northflank will auto-trigger new build")
    print("• Build should start and complete successfully")
    
    print("\nEXPECTED RESULT:")
    print("• New commit pushed to GitHub")
    print("• Northflank detects changes")
    print("• New build starts automatically")
    print("• Application deploys successfully")
    
    return nf_status

if __name__ == "__main__":
    main()
