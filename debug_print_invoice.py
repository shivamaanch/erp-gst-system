"""
Debug the exact enhanced invoice print route
"""

def debug_print_invoice():
    """Debug what happens in the print_invoice route"""
    
    print("🔍 Debugging Enhanced Invoice Print Route")
    print("=" * 50)
    
    # Import and setup
    import sys
    sys.path.append('f:/erp')
    
    from app import create_app
    from extensions import db
    from models import Bill, BillItem, MilkTransaction, Party, Company
    
    app = create_app()
    
    with app.app_context():
        # Simulate the print_invoice route logic
        cid = 2  # Company ID from the database
        bill_id = 1  # Assuming the first bill
        
        print(f"📋 Looking for Bill ID: {bill_id}, Company ID: {cid}")
        
        # Get bill (same as route)
        bill = Bill.query.filter_by(id=bill_id, company_id=cid).first()
        if not bill:
            print("❌ Bill not found!")
            return
        
        print(f"✅ Found bill: {bill.bill_no}")
        print(f"   Type: {bill.bill_type}")
        print(f"   Party ID: {bill.party_id}")
        print(f"   Taxable Amount: {bill.taxable_amount}")
        
        # Get party (same as route)
        party = Party.query.get(bill.party_id)
        print(f"✅ Party: {party.name if party else 'None'}")
        
        # Get company (same as route)
        company = Company.query.get(cid)
        print(f"✅ Company: {company.name if company else 'None'}")
        
        # Get bill items (same as route)
        items = BillItem.query.filter_by(bill_id=bill_id).all()
        print(f"✅ BillItems found: {len(items)}")
        
        for i, item in enumerate(items):
            print(f"   Item {i+1}:")
            print(f"     ID: {item.id}")
            print(f"     Qty: {item.qty}")
            print(f"     Rate: {item.rate}")
            print(f"     Taxable Amount: {item.taxable_amount}")
            print(f"     GST Rate: {item.gst_rate}")
            print(f"     Item ID: {item.item_id}")
            print(f"     Item Name: {item.item.name if item.item else 'None'}")
        
        # Check for milk transaction
        milk_txn = MilkTransaction.query.filter_by(bill_id=bill_id).first()
        print(f"✅ Milk Transaction: {'Yes' if milk_txn else 'None'}")
        if milk_txn:
            print(f"   Milk Txn ID: {milk_txn.id}")
            print(f"   Qty: {milk_txn.qty_liters}")
            print(f"   Rate: {milk_txn.rate}")
            print(f"   Amount: {milk_txn.amount}")
        
        # Check if there are any duplicate BillItems due to joins
        print("\n🔍 Checking for potential query issues...")
        
        # Try different query methods
        print("Method 1: filter_by")
        items1 = BillItem.query.filter_by(bill_id=bill_id).all()
        print(f"   Count: {len(items1)}")
        
        print("Method 2: filter")
        items2 = BillItem.query.filter(BillItem.bill_id == bill_id).all()
        print(f"   Count: {len(items2)}")
        
        print("Method 3: Raw SQL")
        result = db.session.execute("SELECT COUNT(*) FROM bill_items WHERE bill_id = ?", (bill_id,))
        count = result.scalar()
        print(f"   Count: {count}")
        
        # Check for any orphaned BillItems
        print("\n🔍 Checking for orphaned BillItems...")
        all_items = BillItem.query.all()
        orphaned = [item for item in all_items if not Bill.query.get(item.bill_id)]
        print(f"   Orphaned BillItems: {len(orphaned)}")
        
        if orphaned:
            for item in orphaned:
                print(f"     Item ID: {item.id}, Bill ID: {item.bill_id} (missing)")

if __name__ == "__main__":
    debug_print_invoice()
