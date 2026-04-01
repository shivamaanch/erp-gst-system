"""
Check all bills and their company IDs
"""

def check_all_bills():
    """Check all bills in the database"""
    
    print("🔍 Checking All Bills")
    print("=" * 30)
    
    # Import and setup
    import sys
    sys.path.append('f:/erp')
    
    from app import create_app
    from extensions import db
    from models import Bill, BillItem
    
    app = create_app()
    
    with app.app_context():
        # Get all bills
        bills = Bill.query.all()
        
        print(f"📊 Total bills: {len(bills)}")
        
        for bill in bills:
            items = BillItem.query.filter_by(bill_id=bill.id).all()
            print(f"🧾 Bill {bill.bill_no} (ID: {bill.id})")
            print(f"   Company ID: {bill.company_id}")
            print(f"   Party ID: {bill.party_id}")
            print(f"   Type: {bill.bill_type}")
            print(f"   BillItems: {len(items)}")
            print()

if __name__ == "__main__":
    check_all_bills()
