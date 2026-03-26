#!/bin/bash
# Hotfix for Jinja2 Template Error
echo "Applying hotfix for Jinja2 template error..."

# 1. Stop application (if needed)
echo "Stopping application..."
pkill -f "python app.py" || true
sleep 2

# 2. Backup current files
echo "Backing up current files..."
mkdir -p backups/hotfix_20260326_161249
cp -r templates backups/hotfix_20260326_161249/ 2>/dev/null || true
cp modules/milk.py backups/hotfix_20260326_161249/ 2>/dev/null || true

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
