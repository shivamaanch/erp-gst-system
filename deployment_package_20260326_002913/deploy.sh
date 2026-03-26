#!/bin/bash
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
