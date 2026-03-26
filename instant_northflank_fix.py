#!/usr/bin/env python3
"""
Instant Northflank Fix - One Command Solution
Copy this entire script and run it in the Northflank SSH terminal
"""

# INSTANT FIX SCRIPT - Copy and paste this entire block into Northflank SSH terminal

instant_fix = '''
#!/bin/bash
# Instant Northflank Database Fix

echo "Starting instant database fix..."

# Pull latest code
cd /app
git pull origin main

# Run database fix
python live_db_fix.py

# Restart application
echo "Fix completed! Application should restart automatically..."
'''

print("COPY AND PASTE THIS INTO NORTHLANK SSH TERMINAL:")
print("=" * 60)
print(instant_fix)
print("=" * 60)

print("\nOR RUN THESE COMMANDS MANUALLY:")
print("1. SSH: ssh p01--accts--gzfb6r9tnqwp.code.run")
print("2. cd /app")
print("3. git pull origin main")
print("4. python live_db_fix.py")

print("\nEXPECTED OUTPUT:")
print("Starting database fix...")
print("Added voucher_no to bills table")
print("Added voucher_no to milk_transactions table")
print("Database fix completed!")

print("\nThis will fix the voucher_no column issue immediately!")
