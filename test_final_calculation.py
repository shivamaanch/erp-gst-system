"""
Test the final corrected Milk Chief calculation
"""

def test_final_corrected_calculation():
    """Test the final corrected calculation to match Milk Chief exactly"""
    
    print("🧪 Testing Final Corrected Milk Chief Calculation")
    print("=" * 50)
    
    # Test data
    milk_kg = 897
    fat_percent = 4.3
    clr = 29.5
    rate_per_100kg = 4850
    
    print(f"📝 Input Data:")
    print(f"   Milk: {milk_kg} kg")
    print(f"   FAT: {fat_percent}%")
    print(f"   CLR: {clr}")
    print(f"   Rate: ₹{rate_per_100kg}/100kg")
    print()
    
    # SNF calculation with Milk Chief adjustment
    snf_richmond = (clr / 4) + (0.20 * fat_percent) + 0.14
    snf_adjusted = round(snf_richmond, 3) - 0.005
    snf_adjusted = round(snf_adjusted, 3)
    
    print(f"✅ SNF Calculation:")
    print(f"   Richmond Formula: {snf_richmond:.6f}%")
    print(f"   Milk Chief Adjusted: {snf_adjusted:.3f}%")
    print()
    
    # Component weights
    bf_kgs = round(milk_kg * fat_percent / 100, 3)
    snf_kgs = round(milk_kg * snf_adjusted / 100, 3)
    
    print(f"✅ Component Weights:")
    print(f"   BF Kgs: {bf_kgs:.3f}")
    print(f"   SNF Kgs: {snf_kgs:.3f}")
    print()
    
    # Component rates (60:40 split)
    fat_share = 0.60
    snf_share = 0.40
    std_fat_kg = 6.5
    std_snf_kg = 8.5
    
    bf_rate = (rate_per_100kg * fat_share) / std_fat_kg
    snf_rate = (rate_per_100kg * snf_share) / std_snf_kg
    
    print(f"✅ Component Rates:")
    print(f"   BF Rate: ₹{bf_rate:.2f}/kg")
    print(f"   SNF Rate: ₹{snf_rate:.2f}/kg")
    print()
    
    # Final amount
    bf_amount = bf_kgs * bf_rate
    snf_amount = snf_kgs * snf_rate
    total_amount = bf_amount + snf_amount
    
    print(f"✅ Final Amount:")
    print(f"   BF Amount: ₹{bf_amount:.2f}")
    print(f"   SNF Amount: ₹{snf_amount:.2f}")
    print(f"   Total Amount: ₹{total_amount:.2f}")
    print()
    
    # Compare with Milk Chief
    milk_chief_expected = 34403.60
    difference = abs(total_amount - milk_chief_expected)
    accuracy = (1 - difference / milk_chief_expected) * 100
    
    print(f"🎯 Milk Chief Comparison:")
    print(f"   Expected: ₹{milk_chief_expected:.2f}")
    print(f"   Our Result: ₹{total_amount:.2f}")
    print(f"   Difference: ₹{difference:.2f}")
    print(f"   Accuracy: {accuracy:.6f}%")
    
    if difference < 1.0:
        print("✅ EXCELLENT! Very close to Milk Chief!")
    elif difference < 5.0:
        print("✅ GOOD! Acceptable accuracy")
    else:
        print("❌ Still needs improvement")
    
    print()
    print("📊 Expected Milk Statement Values:")
    print(f"   Avg FAT%: {fat_percent:.1f}%")
    print(f"   Avg SNF%: {snf_adjusted:.3f}%")
    print(f"   Daily Rate: ₹{rate_per_100kg}")
    print(f"   Amount: ₹{total_amount:.2f}")

if __name__ == "__main__":
    test_final_corrected_calculation()
