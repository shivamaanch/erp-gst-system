#!/bin/bash
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
