"""
Debug cumulative balance calculation
"""

def debug_cumulative_balance():
    """Debug how the cumulative balance should work"""
    
    print("🔍 Debugging Cumulative Balance Calculation")
    print("=" * 50)
    
    # Import and setup
    import sys
    sys.path.append('f:/erp')
    
    from app import create_app
    from extensions import db
    from models import CashBook
    from datetime import datetime
    
    app = create_app()
    
    with app.app_context():
        # Get all entries in chronological order
        all_entries = CashBook.query.order_by(CashBook.transaction_date.asc(), CashBook.id.asc()).all()
        
        print("📊 ALL CASH BOOK ENTRIES (Chronological):")
        print("-" * 80)
        print(f"{'Date':<12} {'Voucher':<15} {'Type':<8} {'Amount':<10} {'Narration':<25} {'Cumulative':<10}")
        print("-" * 80)
        
        cumulative_balance = 0.0
        
        for entry in all_entries:
            # Calculate cumulative balance
            if entry.transaction_type == 'Receipt':
                cumulative_balance += float(entry.amount)
            elif entry.transaction_type == 'Payment':
                cumulative_balance -= float(entry.amount)
            
            print(f"{entry.transaction_date.strftime('%d-%m-%Y'):<12} "
                  f"{entry.voucher_no:<15} "
                  f"{entry.transaction_type:<8} "
                  f"₹{entry.amount:<9.2f} "
                  f"{(entry.narration or '')[:25]:<25} "
                  f"₹{cumulative_balance:<9.2f}")
        
        print("-" * 80)
        print(f"📈 Final Cumulative Balance: ₹{cumulative_balance:.2f}")
        print()
        
        # Now check what the cash book page is calculating
        print("🔍 CHECKING CASH BOOK PAGE LOGIC:")
        print("-" * 50)
        
        # Simulate cash book page logic (with from_date = None)
        from_date = None
        to_date = None
        
        # Get entries for display (same as cash book page)
        query = CashBook.query
        if from_date:
            # ... filter logic
            pass
        if to_date:
            # ... filter logic  
            pass
            
        entries = query.order_by(CashBook.transaction_date.asc(), CashBook.id.asc()).all()
        
        # Calculate opening balance (same as cash book page)
        opening_balance = 0.0
        try:
            if from_date:
                from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
                opening_entries = CashBook.query.filter(
                    CashBook.transaction_date < from_date_obj
                ).all()
            else:
                # If no from_date, get all entries before the first entry shown
                if entries:
                    first_entry_date = entries[0].transaction_date
                    opening_entries = CashBook.query.filter(
                        CashBook.transaction_date < first_entry_date
                    ).all()
                else:
                    opening_entries = []
            
            opening_balance = sum(entry.amount for entry in opening_entries if entry.transaction_type == "Receipt") - \
                          sum(entry.amount for entry in opening_entries if entry.transaction_type == "Payment")
        except:
            pass
        
        print(f"📋 Opening Balance (before first shown entry): ₹{opening_balance:.2f}")
        print()
        
        # Calculate running balance as template does
        running_balance = opening_balance
        print("📋 Template Balance Calculation:")
        print("-" * 50)
        print(f"{'Date':<12} {'Type':<8} {'Amount':<10} {'Running':<10}")
        print("-" * 50)
        print(f"{'Opening':<12} {'':<8} {'':<10} ₹{running_balance:<9.2f}")
        
        for entry in entries:
            cash_received = 0.0
            cash_paid = 0.0
            if entry.transaction_type == 'Receipt':
                cash_received = float(entry.amount)
            elif entry.transaction_type == 'Payment':
                cash_paid = float(entry.amount)
            
            running_balance = running_balance + cash_received - cash_paid
            
            print(f"{entry.transaction_date.strftime('%d-%m-%Y'):<12} "
                  f"{entry.transaction_type:<8} "
                  f"₹{entry.amount:<9.2f} "
                  f"₹{running_balance:<9.2f}")
        
        print("-" * 50)
        print(f"📈 Final Running Balance: ₹{running_balance:.2f}")
        print()
        
        # Compare
        if cumulative_balance == running_balance:
            print("✅ Both calculations match! Balance should be correct.")
        else:
            print(f"❌ Mismatch! Cumulative: ₹{cumulative_balance:.2f} vs Running: ₹{running_balance:.2f}")
            print("   This explains why the balance looks wrong!")

if __name__ == "__main__":
    debug_cumulative_balance()
