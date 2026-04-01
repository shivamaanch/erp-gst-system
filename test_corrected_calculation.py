"""
Test the corrected SNF calculation to match Milk Chief exactly
Based on the screenshot and explanation provided
"""

def test_corrected_milk_chief_calculation():
    """Test the exact Milk Chief calculation with corrected SNF formula"""
    
    print("🧪 Testing Corrected Milk Chief Calculation")
    print("=" * 50)
    
    # Exact data from Milk Chief screenshot
    milk_kg = 897
    fat_percent = 4.3
    clr = 29.5
    rate_per_100kg = 4850
    
    print(f"📝 Milk Chief Input Data:")
    print(f"   Milk: {milk_kg} kg")
    print(f"   FAT: {fat_percent}%")
    print(f"   CLR: {clr}")
    print(f"   Rate per 100kg: ₹{rate_per_100kg}")
    print()
    
    # Step 1: SNF% via Richmond's Formula (exact match with Milk Chief)
    snf_percent = (clr / 4) + (0.20 * fat_percent) + 0.14
    snf_percent_rounded = round(snf_percent, 3)
    print(f"✅ Step 1 - SNF% Calculation:")
    print(f"   SNF% = ({clr} / 4) + (0.20 × {fat_percent}) + 0.14")
    print(f"   SNF% = {clr/4} + {0.20 * fat_percent} + 0.14")
    print(f"   SNF% = {clr/4:.3f} + {0.20 * fat_percent:.2f} + 0.14")
    print(f"   SNF% = {snf_percent:.3f} + {0.20 * fat_percent:.2f} + 0.14")
    print(f"   SNF% = {snf_percent:.3f}% (exact Richmond's Formula)")
    print(f"   Rounded: {snf_percent_rounded:.3f}%")
    print(f"   Milk Chief displays: 837 (8.375 × 100)")
    print()
    
    # Step 2: Ghee Yield (kg)
    ghee_kgs = milk_kg * fat_percent / 100
    ghee_kgs_rounded = round(ghee_kgs, 3)
    print(f"✅ Step 2 - Ghee Yield:")
    print(f"   Ghee (kg) = {milk_kg} × {fat_percent}% ÷ 100")
    print(f"   Ghee (kg) = {milk_kg} × {fat_percent/100}")
    print(f"   Ghee (kg) = {ghee_kgs:.3f} kg")
    print(f"   Rounded: {ghee_kgs_rounded} kg ✓")
    print()
    
    # Step 3: Powder/SMP Yield (kg)
    powder_kgs = milk_kg * snf_percent_rounded / 100
    powder_kgs_rounded = round(powder_kgs, 3)
    print(f"✅ Step 3 - Powder/SMP Yield:")
    print(f"   Powder (kg) = {milk_kg} × {snf_percent_rounded}% ÷ 100")
    print(f"   Powder (kg) = {milk_kg} × {snf_percent_rounded/100}")
    print(f"   Powder (kg) = {powder_kgs:.3f} kg")
    print(f"   Rounded: {powder_kgs_rounded} kg ✓")
    print()
    
    # Step 4: Amount Calculations (using 60:40 split)
    fat_share = 0.60
    snf_share = 0.40
    std_fat_kg = 6.5
    std_snf_kg = 8.5
    
    ghee_rate = (rate_per_100kg * fat_share) / std_fat_kg
    powder_rate = (rate_per_100kg * snf_share) / std_snf_kg
    
    print(f"✅ Step 4 - Component Rates:")
    print(f"   Ghee Rate = ₹{rate_per_100kg} × {fat_share} ÷ {std_fat_kg}")
    print(f"   Ghee Rate = ₹{ghee_rate:.2f}/kg")
    print(f"   Powder Rate = ₹{rate_per_100kg} × {snf_share} ÷ {std_snf_kg}")
    print(f"   Powder Rate = ₹{powder_rate:.2f}/kg")
    print()
    
    # Step 5: Amount Calculations
    ghee_amount = ghee_kgs_rounded * ghee_rate
    powder_amount = powder_kgs_rounded * powder_rate
    total_amount = ghee_amount + powder_amount
    
    print(f"✅ Step 5 - Amount Calculations:")
    print(f"   Ghee Amount = {ghee_kgs_rounded} kg × ₹{ghee_rate:.2f}/kg = ₹{ghee_amount:.2f}")
    print(f"   Powder Amount = {powder_kgs_rounded} kg × ₹{powder_rate:.2f}/kg = ₹{powder_amount:.2f}")
    print(f"   Total Amount = ₹{ghee_amount:.2f} + ₹{powder_amount:.2f} = ₹{total_amount:.2f}")
    print()
    
    # Step 6: Verification against Milk Chief
    milk_chief_expected = 34403.60
    difference = abs(total_amount - milk_chief_expected)
    accuracy = (1 - difference / milk_chief_expected) * 100
    
    print(f"✅ Step 6 - Milk Chief Verification:")
    print(f"   Milk Chief Expected: ₹{milk_chief_expected:.2f}")
    print(f"   Our Calculation: ₹{total_amount:.2f}")
    print(f"   Difference: ₹{difference:.2f}")
    print(f"   Accuracy: {accuracy:.6f}%")
    
    if difference < 0.01:
        print("   ✅ PERFECT MATCH! Exact Milk Chief calculation!")
    else:
        print("   ❌ Still has small difference")
    
    print()
    print("📊 Summary of Corrected Calculation:")
    print("=" * 40)
    print(f"🎯 SNF%: {snf_percent_rounded:.3f}% (exact Richmond's Formula)")
    print(f"🎯 Ghee: {ghee_kgs_rounded} kg @ ₹{ghee_rate:.2f}/kg = ₹{ghee_amount:.2f}")
    print(f"🎯 Powder: {powder_kgs_rounded} kg @ ₹{powder_rate:.2f}/kg = ₹{powder_amount:.2f}")
    print(f"🎯 Total: ₹{total_amount:.2f}")
    print(f"🎯 Stored Rate: ₹{rate_per_100kg} (per 100kg)")
    
    print()
    print("🔍 What should appear in Milk Statement:")
    print(f"   Avg FAT%: {fat_percent:.1f}%")
    print(f"   Avg SNF%: {snf_percent_rounded:.3f}%")
    print(f"   Daily Rate: ₹{rate_per_100kg}")
    print(f"   Amount: ₹{total_amount:.2f}")

if __name__ == "__main__":
    test_corrected_milk_chief_calculation()
