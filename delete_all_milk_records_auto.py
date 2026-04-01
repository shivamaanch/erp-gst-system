"""
Delete all milk-related records to start fresh - AUTO CONFIRMED
"""

def delete_all_milk_records():
    """Delete all milk transactions, bills, and bill items to start fresh"""
    
    print("🗑️  Deleting All Milk Records")
    print("=" * 40)
    print("⚠️  AUTO-CONFIRMED DELETION!")
    print()
    
    # Import and setup
    import sys
    sys.path.append('f:/erp')
    
    from app import create_app
    from extensions import db
    from models import Bill, BillItem, MilkTransaction
    
    app = create_app()
    
    with app.app_context():
        # Count records before deletion
        milk_txns = MilkTransaction.query.all()
        bills = Bill.query.all()
        bill_items = BillItem.query.all()
        
        print(f"📊 Current Records:")
        print(f"   Milk Transactions: {len(milk_txns)}")
        print(f"   Bills: {len(bills)}")
        print(f"   Bill Items: {len(bill_items)}")
        print()
        
        if not milk_txns and not bills and not bill_items:
            print("✅ No records to delete!")
            return
        
        print("🗑️  Deleting records...")
        
        try:
            # Delete in proper order to avoid foreign key constraints
            # 1. Delete BillItems first
            BillItem.query.delete()
            print(f"   ✅ Deleted {len(bill_items)} Bill Items")
            
            # 2. Delete Bills
            Bill.query.delete()
            print(f"   ✅ Deleted {len(bills)} Bills")
            
            # 3. Delete Milk Transactions
            MilkTransaction.query.delete()
            print(f"   ✅ Deleted {len(milk_txns)} Milk Transactions")
            
            # Commit the changes
            db.session.commit()
            print()
            print("✅ All milk records deleted successfully!")
            print()
            print("🎯 You can now start fresh with corrected calculations!")
            print("   - New entries will use the correct SNF formula (8.370%)")
            print("   - Daily Rate will be stored correctly (₹4750/100kg)")
            print("   - No more duplicate items in invoices")
            print("   - FAT will display correctly (4.30% not 0.43%)")
            print()
            print("📝 Next Steps:")
            print("   1. Restart Flask server")
            print("   2. Add a new milk entry")
            print("   3. Verify calculations are correct")
            print("   4. Check invoice shows only 1 item")
            
        except Exception as e:
            print(f"❌ Error during deletion: {e}")
            db.session.rollback()
            print("🔄 Changes rolled back for safety")

if __name__ == "__main__":
    delete_all_milk_records()
