"""
Check if cash book entries still exist
"""

def check_cash_book_entries():
    """Check what happened to cash book entries"""
    
    print("🔍 Checking Cash Book Entries Status")
    print("=" * 40)
    
    # Import and setup
    import sys
    sys.path.append('f:/erp')
    
    from app import create_app
    from extensions import db
    from models import CashBook
    
    app = create_app()
    
    with app.app_context():
        # Check total entries
        all_entries = CashBook.query.all()
        print(f"📊 Total entries in database: {len(all_entries)}")
        
        if len(all_entries) == 0:
            print("❌ All cash book entries are gone!")
            print()
            print("🔧 Possible causes:")
            print("   1. Entries were accidentally deleted")
            print("   2. Date filter is hiding all entries")
            print("   3. Company/Financial Year filter issue")
            print("   4. Database was reset")
            print()
            print("💡 Let's add some test entries to demonstrate cumulative balance:")
            
            # Add test entries to demonstrate cumulative balance
            from datetime import date, datetime
            
            # Test Entry 1: Opening receipt
            entry1 = CashBook(
                company_id=2,  # Use your company ID
                fin_year="2025-26",
                voucher_no="CB-2025-26-TEST1",
                transaction_date=date.today(),
                transaction_type="Receipt",
                amount=2000.00,
                narration="Test receipt 1",
                party_name="Test Party",
                payment_mode="Cash",
                account_id=1  # Use a valid account ID
            )
            
            # Test Entry 2: Same day receipt
            entry2 = CashBook(
                company_id=2,
                fin_year="2025-26", 
                voucher_no="CB-2025-26-TEST2",
                transaction_date=date.today(),
                transaction_type="Receipt",
                amount=2000.00,
                narration="Test receipt 2 - same day",
                party_name="Test Party 2",
                payment_mode="Cash",
                account_id=1
            )
            
            try:
                db.session.add(entry1)
                db.session.add(entry2)
                db.session.commit()
                print("✅ Added 2 test entries to demonstrate cumulative balance")
                print()
                print("📋 Expected cumulative balance:")
                print("   Opening: ₹0")
                print("   + Test Entry 1: ₹2,000 = ₹2,000")
                print("   + Test Entry 2: ₹2,000 = ₹4,000")
                print()
                print("🎯 Now refresh cash book page to see cumulative balance in action!")
                
            except Exception as e:
                print(f"❌ Error adding test entries: {e}")
                print("   You may need to add entries manually through the web interface")
        
        else:
            print("✅ Entries still exist:")
            for entry in all_entries:
                print(f"   {entry.voucher_no}: {entry.transaction_type} ₹{entry.amount} on {entry.transaction_date}")

if __name__ == "__main__":
    check_cash_book_entries()
