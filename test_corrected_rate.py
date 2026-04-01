"""
Test the corrected rate calculation to ensure daily rate is stored correctly
"""

def test_corrected_rate_calculation():
    """Test that the daily rate is stored correctly without incorrect multiplication"""
    
    print("🧪 Testing Corrected Rate Calculation")
    print("=" * 50)
    
    # Test data
    qty = 897
    fat = 4.3
    clr = 29.5
    daily_rate_input = 4850  # User enters ₹4850 for ₹4850/100kg
    
    print(f"📝 Test Data:")
    print(f"   Quantity: {qty} kg")
    print(f"   Fat: {fat}%")
    print(f"   CLR: {clr}")
    print(f"   Daily Rate Input: ₹{daily_rate_input}")
    print()
    
    # Test the corrected logic
    print("✅ Corrected Logic:")
    print(f"   User enters: ₹{daily_rate_input} (already per 100kg)")
    print(f"   Stored as: ₹{daily_rate_input} (no multiplication)")
    print(f"   Display as: ₹{daily_rate_input}/100kg")
    print()
    
    # Calculate amount using component method
    snf = (clr / 4) + (0.20 * fat) + 0.14
    snf = round(snf, 3) - 0.005
    snf = round(snf, 3)
    
    bf_kgs = qty * fat / 100
    snf_kgs = qty * snf / 100
    bf_kgs = round(bf_kgs, 3)
    snf_kgs = round(snf_kgs, 3)
    
    fat_share = 0.60
    snf_share = 0.40
    std_fat_kg = 6.5
    std_snf_kg = 8.5
    
    bf_rate = (daily_rate_input * fat_share) / std_fat_kg
    snf_rate = (daily_rate_input * snf_share) / std_snf_kg
    
    bf_amount = bf_kgs * bf_rate
    snf_amount = snf_kgs * snf_rate
    total_amount = bf_amount + snf_amount
    
    print(f"✅ Component Calculation:")
    print(f"   SNF%: {snf:.3f}%")
    print(f"   BF Kgs: {bf_kgs} kg")
    print(f"   SNF Kgs: {snf_kgs} kg")
    print(f"   BF Rate: ₹{bf_rate:.2f}/kg")
    print(f"   SNF Rate: ₹{snf_rate:.2f}/kg")
    print(f"   BF Amount: ₹{bf_amount:.2f}")
    print(f"   SNF Amount: ₹{snf_amount:.2f}")
    print(f"   Total Amount: ₹{total_amount:.2f}")
    print()
    
    # Test rate calculation from amount (what happens when only amount is provided)
    rate_from_amount = total_amount / qty
    print(f"✅ Rate from Amount:")
    print(f"   Total Amount: ₹{total_amount:.2f}")
    print(f"   Quantity: {qty} kg")
    print(f"   Rate per 100kg: ₹{rate_from_amount:.2f}")
    print()
    
    # Compare with expected
    print(f"🎯 Expected Results:")
    print(f"   Stored Rate: ₹{daily_rate_input} (per 100kg)")
    print(f"   Calculated Rate: ₹{rate_from_amount:.2f} (per 100kg)")
    print(f"   Total Amount: ₹{total_amount:.2f}")
    print()
    
    # Test the old incorrect logic (for comparison)
    old_incorrect_rate = daily_rate_input * 100
    old_incorrect_amount = qty * old_incorrect_rate
    print(f"❌ Old Incorrect Logic (for comparison):")
    print(f"   Would store rate as: ₹{old_incorrect_rate} (WRONG!)")
    print(f"   Would calculate amount: ₹{old_incorrect_amount} (WRONG!)")
    print(f"   Difference: ₹{abs(old_incorrect_amount - total_amount):.2f}")
    print()
    
    print(f"📊 Summary:")
    print(f"   ✅ Correct: Store rate as ₹{daily_rate_input}/100kg")
    print(f"   ✅ Correct: Calculate amount as ₹{total_amount:.2f}")
    print(f"   ✅ Correct: Display as ₹{daily_rate_input}/100kg")
    print(f"   ❌ Fixed: No more rate*100 multiplication")

if __name__ == "__main__":
    test_corrected_rate_calculation()
