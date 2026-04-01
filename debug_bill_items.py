"""
Debug script to check BillItems for milk bills
"""

def check_bill_items():
    """Check how many BillItems exist for each bill"""
    
    print("🔍 Checking BillItems for Milk Bills")
    print("=" * 40)
    
    # Import and setup
    import sys
    sys.path.append('f:/erp')
    
    from app import create_app
    from extensions import db
    from models import Bill, BillItem, MilkTransaction
    
    app = create_app()
    
    with app.app_context():
        # Get all bills that might be related to milk
        bills = Bill.query.all()
        
        print(f"📊 Total bills found: {len(bills)}")
        print()
        
        for bill in bills:
            # Count BillItems for this bill
            bill_items = BillItem.query.filter_by(bill_id=bill.id).all()
            
            # Check if there's a milk transaction linked
            milk_txn = MilkTransaction.query.filter_by(bill_id=bill.id).first()
            
            print(f"🧾 Bill {bill.bill_no} (ID: {bill.id})")
            print(f"   Type: {bill.bill_type}")
            print(f"   Party: {bill.party.name if bill.party else 'N/A'}")
            print(f"   BillItems: {len(bill_items)}")
            print(f"   Milk Transaction: {'Yes' if milk_txn else 'No'}")
            
            if len(bill_items) > 1:
                print(f"   ⚠️  WARNING: Multiple BillItems found!")
                for i, item in enumerate(bill_items):
                    print(f"      Item {i+1}: Qty={item.qty}, Rate={item.rate}, Amount={item.taxable_amount}")
            
            print()
        
        # Check for potential duplicates
        print("🔍 Checking for potential issues...")
        
        # Find bills with multiple BillItems
        multi_item_bills = []
        for bill in bills:
            item_count = BillItem.query.filter_by(bill_id=bill.id).count()
            if item_count > 1:
                multi_item_bills.append((bill, item_count))
        
        if multi_item_bills:
            print(f"⚠️  Found {len(multi_item_bills)} bills with multiple items:")
            for bill, count in multi_item_bills:
                print(f"   Bill {bill.bill_no}: {count} items")
        else:
            print("✅ No bills with multiple items found")
        
        # Check milk transactions without bills
        milk_txns_without_bills = MilkTransaction.query.filter(MilkTransaction.bill_id.is_(None)).count()
        print(f"📊 Milk transactions without bills: {milk_txns_without_bills}")

if __name__ == "__main__":
    check_bill_items()
