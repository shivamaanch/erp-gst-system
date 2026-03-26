#!/usr/bin/env python3
"""
Database Migration: Add voucher_no columns and populate existing records
"""

from app import app
from extensions import db
from models import Bill, MilkTransaction
from utils.voucher_helper import generate_voucher_number
from sqlalchemy import text

def add_voucher_columns():
    """Add voucher_no columns to tables"""
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            
            # Add voucher_no to bills table if not exists
            bills_columns = [col['name'] for col in inspector.get_columns('bills')]
            if 'voucher_no' not in bills_columns:
                print("📝 Adding voucher_no column to bills table...")
                db.session.execute(text('ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50)'))
                db.session.execute(text('CREATE INDEX idx_bills_voucher_no ON bills(voucher_no)'))
                db.session.commit()
                print("✅ Added voucher_no to bills table")
            else:
                print("ℹ️  voucher_no column already exists in bills table")
            
            # Add voucher_no to milk_transactions table if not exists
            milk_columns = [col['name'] for col in inspector.get_columns('milk_transactions')]
            if 'voucher_no' not in milk_columns:
                print("📝 Adding voucher_no column to milk_transactions table...")
                db.session.execute(text('ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50)'))
                db.session.execute(text('CREATE INDEX idx_milk_transactions_voucher_no ON milk_transactions(voucher_no)'))
                db.session.commit()
                print("✅ Added voucher_no to milk_transactions table")
            else:
                print("ℹ️  voucher_no column already exists in milk_transactions table")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding columns: {e}")
            return False
        
        return True

def populate_voucher_numbers():
    """Populate voucher numbers for existing records"""
    with app.app_context():
        try:
            # Populate Bills
            print("\n📋 Populating voucher numbers for Bills...")
            bills = Bill.query.filter(
                (Bill.voucher_no == None) | (Bill.voucher_no == '')
            ).order_by(Bill.bill_date, Bill.id).all()
            
            for bill in bills:
                voucher_no = generate_voucher_number(
                    bill.company_id,
                    bill.fin_year,
                    bill.bill_type
                )
                bill.voucher_no = voucher_no
                print(f"  ✓ Bill {bill.bill_no} → {voucher_no}")
            
            db.session.commit()
            print(f"✅ Updated {len(bills)} bills with voucher numbers")
            
            # Populate Milk Transactions
            print("\n🥛 Populating voucher numbers for Milk Transactions...")
            milk_txns = MilkTransaction.query.filter(
                (MilkTransaction.voucher_no == None) | (MilkTransaction.voucher_no == '')
            ).order_by(MilkTransaction.txn_date, MilkTransaction.id).all()
            
            for txn in milk_txns:
                voucher_no = generate_voucher_number(
                    txn.company_id,
                    txn.fin_year,
                    'Milk'
                )
                txn.voucher_no = voucher_no
                print(f"  ✓ Milk Entry {txn.id} → {voucher_no}")
            
            db.session.commit()
            print(f"✅ Updated {len(milk_txns)} milk transactions with voucher numbers")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error populating voucher numbers: {e}")
            return False
        
        return True

def main():
    """Run migration"""
    print("🚀 Starting Voucher Number Migration...")
    print("=" * 50)
    
    # Step 1: Add columns
    if not add_voucher_columns():
        print("\n❌ Migration failed at column addition step")
        return
    
    # Step 2: Populate voucher numbers
    if not populate_voucher_numbers():
        print("\n❌ Migration failed at population step")
        return
    
    print("\n" + "=" * 50)
    print("✅ Voucher Number Migration Completed Successfully!")
    print("\nVoucher Format:")
    print("  Sales:    SV/2025-26/0001")
    print("  Purchase: PV/2025-26/0001")
    print("  Milk:     MV/2025-26/0001")
    print("  Journal:  JV/2025-26/0001")

if __name__ == "__main__":
    main()
