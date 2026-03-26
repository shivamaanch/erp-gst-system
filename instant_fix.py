#!/usr/bin/env python3
"""
Instant CLR Column Fix - Copy and paste this into Northflank SSH terminal
"""

instant_fix = '''python -c "import sys;sys.path.insert(0,'/app');from app import app;from extensions import db;from sqlalchemy import text;app.app_context().push();db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN clr DECIMAL(10,2) DEFAULT 0.0'));db.session.commit();print('CLR column added successfully!')"'''

print("COPY AND PASTE THIS INTO NORTHFLANK SSH TERMINAL:")
print("=" * 80)
print(instant_fix)
print("=" * 80)

print("\nThis will immediately fix the CLR column issue!")
print("After running this, the milk entries page will work!")
