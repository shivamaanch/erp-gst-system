#!/bin/bash
echo "Starting Live Deployment..."

# 1. Stop application
pkill -f "python app.py" || true
sleep 2

# 2. Backup database
python -c "
from app import app
from extensions import db
from datetime import datetime
import shutil

with app.app_context():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/live_backup_{timestamp}.db'
    shutil.copy2('instance/erp.db', backup_file)
    print(f'Backup created: {backup_file}')
"

# 3. Run migrations
python add_voucher_numbers.py
python initialize_default_accounts.py

# 4. Start application
nohup python app.py > app.log 2>&1 &

echo "Deployment completed!"
echo "Application running..."
