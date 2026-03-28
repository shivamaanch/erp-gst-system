#!/bin/bash
# Deployment script for ERP system on Northflank

echo "🚀 Starting ERP deployment..."

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Install dependencies if needed
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️ Running database migrations..."
python migrations/live_server_complete_migration.py

# Restart the application
echo "🔄 Restarting application..."
# The application will be automatically restarted by the deployment system

echo "✅ Deployment completed!"
