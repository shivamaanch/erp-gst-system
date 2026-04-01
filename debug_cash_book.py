"""
Debug cash book entries to check transaction types and amounts
"""

def debug_cash_book():
    """Debug cash book entries to see what's wrong"""
    
    print("🔍 Debugging Cash Book Entries")
    print("=" * 40)
    
    # Import and setup
    import sys
    sys.path.append('f:/erp')
    
    from app import create_app
    from extensions import db
    from models import CashBook
    
    app = create_app()
    
    with app.app_context():
        # Get all cash book entries
        entries = CashBook.query.order_by(CashBook.transaction_date.asc(), CashBook.id.asc()).all()
        
        print(f"📊 Total entries: {len(entries)}")
        print()
        
        running_balance = 0.0
        
        print("📋 Detailed Entry Analysis:")
        print("-" * 80)
        print(f"{'Date':<12} {'Voucher':<15} {'Type':<8} {'Amount':<10} {'Party':<20} {'Narration':<25} {'Balance':<10}")
        print("-" * 80)
        
        for i, entry in enumerate(entries):
            print(f"{entry.transaction_date.strftime('%d-%m-%Y'):<12} "
                  f"{entry.voucher_no:<15} "
                  f"{entry.transaction_type:<8} "
                  f"₹{entry.amount:<9.2f} "
                  f"{(entry.party_name or '')[:20]:<20} "
                  f"{(entry.narration or '')[:25]:<25} "
                  f"{'':<10}")
            
            # Calculate running balance
            if entry.transaction_type == 'Receipt':
                running_balance += float(entry.amount)
                print(f"{'':12} {'':15} {'':8} {'+₹':<10} {'':20} {'':25} ₹{running_balance:<9.2f}")
            elif entry.transaction_type == 'Payment':
                running_balance -= float(entry.amount)
                print(f"{'':12} {'':15} {'':8} {'-₹':<10} {'':20} {'':25} ₹{running_balance:<9.2f}")
            else:
                print(f"{'':12} {'':15} {'':8} {'?':<10} {'':20} {'':25} ₹{running_balance:<9.2f}")
            
            print("-" * 80)
        
        print()
        print("🎯 Issues Found:")
        
        # Check for suspicious entries
        suspicious = []
        for entry in entries:
            narration = (entry.narration or '').lower()
            if 'received' in narration and entry.transaction_type == 'Payment':
                suspicious.append((entry.voucher_no, "Says 'received' but marked as Payment"))
            elif 'paid' in narration and entry.transaction_type == 'Receipt':
                suspicious.append((entry.voucher_no, "Says 'paid' but marked as Receipt"))
        
        if suspicious:
            print("⚠️  Suspicious entries:")
            for voucher, issue in suspicious:
                print(f"   {voucher}: {issue}")
        else:
            print("✅ No suspicious entries found")
        
        print()
        print(f"📊 Final Balance: ₹{running_balance:.2f}")

if __name__ == "__main__":
    debug_cash_book()
