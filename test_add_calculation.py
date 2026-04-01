"""
Direct test of the add milk route calculation logic
"""

def test_add_milk_calculation():
    """Test the exact calculation logic used in add milk route"""
    
    print("🧪 Testing Add Milk Route Calculation Logic")
    print("=" * 50)
    
    # Simulate form data from add milk route
    form_data = {
        "fat": 43,  # User enters 43, will be converted to 4.3
        "clr": 295,  # User enters 295, will be converted to 29.5
        "qty_liters": 897,
        "rate_per_liter": 4850  # Rate per 100kg
    }
    
    print(f"📝 Form Input:")
    print(f"   Fat: {form_data['fat']}")
    print(f"   CLR: {form_data['clr']}")
    print(f"   Quantity: {form_data['qty_liters']}")
    print(f"   Rate: {form_data['rate_per_liter']}")
    print()
    
    # Step 1: Convert fat (43 → 4.3)
    fat = float(form_data["fat"])
    fat = fat / 10.0
    print(f"✅ Fat Conversion: {form_data['fat']} → {fat:.2f}%")
    
    # Step 2: Convert CLR (295 → 29.5)
    clr = float(form_data.get("clr", 0))
    if clr > 100:
        clr = clr / 10.0
    print(f"✅ CLR Conversion: {form_data['clr']} → {clr:.1f}")
    
    # Step 3: Calculate SNF using Richmond's Formula with Milk Chief adjustment
    snf = (clr / 4) + (0.20 * fat) + 0.14
    snf = round(snf, 3) - 0.005
    snf = round(snf, 3)
    print(f"✅ SNF Calculation: {snf:.3f}%")
    
    # Step 4: Component calculation (60:40 split)
    daily_rate = float(form_data["rate_per_liter"])
    rate_per_100kg = daily_rate  # This is already rate per 100kg
    
    fat_share = 0.60
    snf_share = 0.40
    std_fat_kg = 6.5
    std_snf_kg = 8.5
    
    bf_rate = (rate_per_100kg * fat_share) / std_fat_kg
    snf_rate = (rate_per_100kg * snf_share) / std_snf_kg
    print(f"✅ BF Rate: ₹{bf_rate:.2f}/kg")
    print(f"✅ SNF Rate: ₹{snf_rate:.2f}/kg")
    
    # Step 5: Component weights
    qty = float(form_data["qty_liters"])
    bf_kgs = qty * fat / 100.0
    snf_kgs = qty * snf / 100.0
    bf_kgs = round(bf_kgs, 3)
    snf_kgs = round(snf_kgs, 3)
    print(f"✅ BF Kgs: {bf_kgs:.3f}")
    print(f"✅ SNF Kgs: {snf_kgs:.3f}")
    
    # Step 6: Final amount
    bf_amount = bf_kgs * bf_rate
    snf_amount = snf_kgs * snf_rate
    final_amount = bf_amount + snf_amount
    print(f"✅ BF Amount: ₹{bf_amount:.2f}")
    print(f"✅ SNF Amount: ₹{snf_amount:.2f}")
    print(f"✅ Final Amount: ₹{final_amount:.2f}")
    
    # Step 7: Rate storage
    stored_rate = daily_rate  # Store as rate per 100kg
    print(f"✅ Stored Rate: ₹{stored_rate:.2f} (per 100kg)")
    
    print()
    print("📊 Expected Results:")
    print("=" * 30)
    print(f"🎯 Fat: {fat:.2f}%")
    print(f"🎯 SNF: {snf:.3f}%")
    print(f"🎯 Rate: ₹{stored_rate:.2f} (per 100kg)")
    print(f"🎯 Amount: ₹{final_amount:.2f}")
    
    # Compare with Milk Chief expected
    milk_chief_expected = 34403.60
    difference = abs(final_amount - milk_chief_expected)
    accuracy = (1 - difference / milk_chief_expected) * 100
    
    print()
    print("🎯 Milk Chief Comparison:")
    print(f"   Expected: ₹{milk_chief_expected:.2f}")
    print(f"   Calculated: ₹{final_amount:.2f}")
    print(f"   Difference: ₹{difference:.2f}")
    print(f"   Accuracy: {accuracy:.5f}%")
    
    if difference < 1.0:
        print("✅ PASS: Add milk route calculation is correct!")
    else:
        print("❌ FAIL: Add milk route calculation has issues")
    
    print()
    print("🔍 What should appear in Milk Statement:")
    print(f"   Avg FAT%: {fat:.2f}%")
    print(f"   Avg SNF%: {snf:.3f}%")
    print(f"   Daily Rate: ₹{stored_rate:.2f}")
    print(f"   Amount: ₹{final_amount:.2f}")

if __name__ == "__main__":
    test_add_milk_calculation()
