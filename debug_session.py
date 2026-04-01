"""
Debug session vs entry mismatch
"""

def debug_session_mismatch():
    """Debug why entries aren't showing on web page"""
    
    print("🔍 Debugging Session vs Entry Mismatch")
    print("=" * 45)
    
    # Import and setup
    import sys
    sys.path.append('f:/erp')
    
    from app import create_app
    from extensions import db
    from models import CashBook
    
    app = create_app()
    
    with app.app_context():
        # Get all entries with their company/fy details
        entries = CashBook.query.all()
        
        print("📊 All Cash Book Entries:")
        for entry in entries:
            print(f"   {entry.voucher_no}: Company {entry.company_id}, FY {entry.fin_year}, "
                  f"Date {entry.transaction_date}, Amount ₹{entry.amount}")
        
        print()
        print("🎯 The web page filters by:")
        print("   - company_id (from session)")
        print("   - fin_year (from session)") 
        print("   - from_date/to_date (if specified)")
        print()
        print("💡 Possible issues:")
        print("   1. Wrong company_id in session")
        print("   2. Wrong fin_year in session")
        print("   3. Date filter excluding entries")
        print("   4. Session expired")
        
        print()
        print("🔧 SOLUTIONS:")
        print()
        print("Option 1: Check and fix session")
        print("   - Go to Company Management")
        print("   - Select your company 'SHIVAM GROVER AND ASSOCIATES'")
        print("   - Make sure FY 2025-26 is selected")
        print()
        print("Option 2: Clear date filters")
        print("   - Clear From Date and To Date fields")
        print("   - Click Search to show all entries")
        print()
        print("Option 3: Add new test entry")
        print("   - Click 'Add Cash Entry' in cash book")
        print("   - Add a small test entry (₹100)")
        print("   - See if it shows cumulative balance correctly")

if __name__ == "__main__":
    debug_session_mismatch()
