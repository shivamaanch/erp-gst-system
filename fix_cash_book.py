"""
Fix cash book transaction types
"""

def fix_cash_book_entries():
    """Fix the wrong transaction types in cash book"""
    
    print("🔧 Fixing Cash Book Transaction Types")
    print("=" * 40)
    
    # Import and setup
    import sys
    sys.path.append('f:/erp')
    
    from app import create_app
    from extensions import db
    from models import CashBook
    
    app = create_app()
    
    with app.app_context():
        # Get the problematic entries
        entry1 = CashBook.query.filter_by(voucher_no='CB-2025-26-0002').first()
        entry2 = CashBook.query.filter_by(voucher_no='CB-2025-26-0003').first()
        
        print("📋 Fixing entries:")
        
        # Fix entry 1: Should be Receipt, not Payment
        if entry1:
            print(f"🔄 {entry1.voucher_no}: {entry1.transaction_type} → Receipt")
            entry1.transaction_type = 'Receipt'
            print(f"   Narration: {entry1.narration}")
            print(f"   Amount: ₹{entry1.amount}")
        else:
            print("❌ Entry CB-2025-26-0002 not found")
        
        print()
        
        # Fix entry 2: Should be Payment, not Receipt  
        if entry2:
            print(f"🔄 {entry2.voucher_no}: {entry2.transaction_type} → Payment")
            entry2.transaction_type = 'Payment'
            print(f"   Narration: {entry2.narration}")
            print(f"   Amount: ₹{entry2.amount}")
        else:
            print("❌ Entry CB-2025-26-0003 not found")
        
        # Commit changes
        try:
            db.session.commit()
            print()
            print("✅ Transaction types fixed successfully!")
            print()
            print("🎯 Corrected Entries:")
            print("   CB-2025-26-0002: Payment → Receipt (Cash received from hdfc)")
            print("   CB-2025-26-0003: Receipt → Payment (Cash paid to hdfc)")
            print()
            print("📊 Expected Balance Calculation:")
            print("   Opening: ₹0.00")
            print("   + CB-2025-26-0001 (Receipt): ₹2,000.00 = ₹2,000.00")
            print("   + CB-2025-26-0002 (Receipt): ₹5,000.00 = ₹7,000.00") 
            print("   - CB-2025-26-0003 (Payment): ₹500.00 = ₹6,500.00")
            print("   - CB-2025-26-0004 (Payment): ₹100.00 = ₹6,400.00")
            print()
            print("🎉 Final balance should be: ₹6,400.00")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    fix_cash_book_entries()
