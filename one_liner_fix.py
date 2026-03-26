#!/usr/bin/env python3
"""
One-Liner Northflank Fix - Copy and paste this single line
"""

one_liner = '''python -c "import sys;sys.path.insert(0,'/app');from app import app;from extensions import db;from sqlalchemy import text;app.app_context().push();db.session.execute(text('ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50)'));db.session.commit();db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50)'));db.session.commit();print('Database fix completed!')"'''

print("COPY AND PASTE THIS SINGLE LINE INTO NORTHFLANK SSH TERMINAL:")
print("=" * 80)
print(one_liner)
print("=" * 80)

print("\nOR RUN THESE COMMANDS:")
print("ssh p01--accts--gzfb6r9tnqwp.code.run")
print("cd /app")
print("git pull origin main")
print("Then paste the one-liner above")

print("\nThis will fix the database immediately!")
