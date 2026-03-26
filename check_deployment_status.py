#!/usr/bin/env python3
"""
Check Deployment Status - Verify what was pushed and where
"""

import os
import subprocess
from datetime import datetime

def check_local_packages():
    """Check what packages were created locally"""
    print("Checking local deployment packages...")
    
    packages = []
    
    # Look for deployment packages
    for item in os.listdir('.'):
        if item.startswith('deploy_package_'):
            stat = os.stat(item)
            packages.append({
                'name': item,
                'type': 'deployment',
                'created': datetime.fromtimestamp(stat.st_mtime),
                'size': sum(os.path.getsize(os.path.join(dirpath, filename)) 
                          for dirpath, dirnames, filenames in os.walk(item) 
                          for filename in filenames)
            })
        elif item.startswith('production_package_'):
            stat = os.stat(item)
            packages.append({
                'name': item,
                'type': 'production',
                'created': datetime.fromtimestamp(stat.st_mtime),
                'size': sum(os.path.getsize(os.path.join(dirpath, filename)) 
                          for dirpath, dirnames, filenames in os.walk(item) 
                          for filename in filenames)
            })
        elif item.startswith('simple_build_'):
            stat = os.stat(item)
            packages.append({
                'name': item,
                'type': 'build_fix',
                'created': datetime.fromtimestamp(stat.st_mtime),
                'size': sum(os.path.getsize(os.path.join(dirpath, filename)) 
                          for dirpath, dirnames, filenames in os.walk(item) 
                          for filename in filenames)
            })
        elif item.startswith('hotfix_'):
            stat = os.stat(item)
            packages.append({
                'name': item,
                'type': 'hotfix',
                'created': datetime.fromtimestamp(stat.st_mtime),
                'size': sum(os.path.getsize(os.path.join(dirpath, filename)) 
                          for dirpath, dirnames, filenames in os.walk(item) 
                          for filename in filenames)
            })
    
    # Sort by creation time
    packages.sort(key=lambda x: x['created'], reverse=True)
    
    print(f"Found {len(packages)} packages:")
    for pkg in packages:
        print(f"  {pkg['type']:12} | {pkg['name']:30} | {pkg['created']} | {pkg['size']/1024:.1f}KB")
    
    return packages

def check_git_status():
    """Check git status to see what was committed"""
    print("\nChecking git status...")
    
    try:
        # Check if git repository
        if not os.path.exists('.git'):
            print("  Not a git repository")
            return None
        
        # Check git status
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip():
            print("  Uncommitted changes:")
            for line in result.stdout.strip().split('\n'):
                print(f"    {line}")
        else:
            print("  Working directory clean")
        
        # Check last commit
        result = subprocess.run(['git', 'log', '-1', '--oneline'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print(f"  Last commit: {result.stdout.strip()}")
        
        # Check remote
        result = subprocess.run(['git', 'remote', '-v'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print("  Remotes:")
            for line in result.stdout.strip().split('\n'):
                print(f"    {line}")
        
        return True
        
    except Exception as e:
        print(f"  Git error: {e}")
        return False

def check_live_connection():
    """Check if we can connect to live environment"""
    print("\nChecking live environment connection...")
    
    # Check if there are any deployment scripts that show where it was deployed
    deployment_files = []
    for item in os.listdir('.'):
        if item.endswith('_report.json'):
            deployment_files.append(item)
        elif item.endswith('_checklist.md'):
            deployment_files.append(item)
    
    if deployment_files:
        print("  Found deployment documentation:")
        for f in deployment_files:
            print(f"    {f}")
    else:
        print("  No deployment documentation found")
    
    return deployment_files

def create_deployment_summary():
    """Create comprehensive deployment summary"""
    print("\n" + "=" * 60)
    print("DEPLOYMENT STATUS SUMMARY")
    print("=" * 60)
    
    # Check packages
    packages = check_local_packages()
    
    # Check git
    git_status = check_git_status()
    
    # Check deployment docs
    docs = check_live_connection()
    
    # Create summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'local_packages': packages,
        'git_status': git_status,
        'deployment_docs': docs,
        'recommendations': []
    }
    
    # Add recommendations
    if not packages:
        summary['recommendations'].append("No deployment packages found - create one")
    else:
        latest_pkg = packages[0]
        summary['recommendations'].append(f"Use latest package: {latest_pkg['name']}")
    
    if git_status and 'Uncommitted changes' in str(git_status):
        summary['recommendations'].append("Commit changes before deployment")
    
    if not docs:
        summary['recommendations'].append("Document deployment process")
    
    return summary

def main():
    print("CHECKING DEPLOYMENT STATUS")
    print("Verifying what was pushed and where...")
    
    summary = create_deployment_summary()
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT STATUS COMPLETE")
    print("=" * 60)
    
    print("\nCurrent Status:")
    print(f"  Local packages: {len(summary['local_packages'])}")
    print(f"  Git status: {'Clean' if summary['git_status'] else 'Has changes'}")
    print(f"  Deployment docs: {len(summary['deployment_docs'])}")
    
    print("\nRecommendations:")
    for rec in summary['recommendations']:
        print(f"  • {rec}")
    
    print("\nNext Steps:")
    if summary['local_packages']:
        latest = summary['local_packages'][0]
        print(f"  1. Use package: {latest['name']}")
        print("  2. Upload to live server")
        print("  3. Run deployment script")
    else:
        print("  1. Create deployment package")
        print("  2. Test locally")
        print("  3. Deploy to live")
    
    return summary

if __name__ == "__main__":
    main()
