"""
Debug the exact Milk Chief calculation to find the small difference
"""

def debug_milk_chief_difference():
    """Debug why there's still a small difference with Milk Chief"""
    
    print("🔍 Debugging Milk Chief Calculation Difference")
    print("=" * 50)
    
    # Milk Chief exact values from screenshot
    milk_kg = 897
    fat_percent = 4.3
    clr = 29.5
    rate_per_100kg = 4850
    
    # Milk Chief exact results
    milk_chief_ghee_kgs = 38.571
    milk_chief_powder_kgs = 75.079
    milk_chief_ghee_rate = 447.68
    milk_chief_powder_rate = 228.23
    milk_chief_ghee_amount = 17267.94
    milk_chief_powder_amount = 17135.66
    milk_chief_total = 34403.60
    
    print(f"📊 Milk Chief Exact Results:")
    print(f"   Ghee Kgs: {milk_chief_ghee_kgs}")
    print(f"   Powder Kgs: {milk_chief_powder_kgs}")
    print(f"   Ghee Rate: ₹{milk_chief_ghee_rate}")
    print(f"   Powder Rate: ₹{milk_chief_powder_rate}")
    print(f"   Ghee Amount: ₹{milk_chief_ghee_amount}")
    print(f"   Powder Amount: ₹{milk_chief_powder_amount}")
    print(f"   Total Amount: ₹{milk_chief_total}")
    print()
    
    # Our calculation
    snf_percent = (clr / 4) + (0.20 * fat_percent) + 0.14
    snf_percent_rounded = round(snf_percent, 3)
    
    our_ghee_kgs = milk_kg * fat_percent / 100
    our_powder_kgs = milk_kg * snf_percent_rounded / 100
    
    # Try different rounding approaches for powder kgs
    powder_kgs_exact = milk_kg * snf_percent / 100
    powder_kgs_round2 = round(powder_kgs_exact, 2)
    powder_kgs_round3 = round(powder_kgs_exact, 3)
    powder_kgs_trunc = int(powder_kgs_exact * 1000) / 1000
    powder_kgs_floor = int(powder_kgs_exact * 100) / 100
    
    print(f"🔍 Powder Kgs Calculation Analysis:")
    print(f"   Exact: {powder_kgs_exact:.6f}")
    print(f"   Round to 2dp: {powder_kgs_round2:.3f}")
    print(f"   Round to 3dp: {powder_kgs_round3:.3f}")
    print(f"   Truncate to 3dp: {powder_kgs_trunc:.3f}")
    print(f"   Floor to 2dp: {powder_kgs_floor:.3f}")
    print(f"   Milk Chief: {milk_chief_powder_kgs:.3f}")
    print()
    
    # Check if Milk Chief uses different SNF precision
    # Let's work backwards from their powder kgs
    implied_snf_percent = (milk_chief_powder_kgs * 100) / milk_kg
    print(f"🔍 Implied SNF% from Milk Chief Powder Kgs:")
    print(f"   Implied SNF% = ({milk_chief_powder_kgs} × 100) ÷ {milk_kg}")
    print(f"   Implied SNF% = {implied_snf_percent:.6f}%")
    print(f"   Richmond Formula: {snf_percent:.6f}%")
    print(f"   Difference: {abs(implied_snf_percent - snf_percent):.6f}%")
    print()
    
    # Try using implied SNF to see if we get their exact results
    test_powder_kgs = milk_kg * implied_snf_percent / 100
    test_ghee_amount = our_ghee_kgs * milk_chief_ghee_rate
    test_powder_amount = test_powder_kgs * milk_chief_powder_rate
    test_total = test_ghee_amount + test_powder_amount
    
    print(f"🧪 Test with Implied SNF%:")
    print(f"   Powder Kgs: {test_powder_kgs:.3f} (vs {milk_chief_powder_kgs:.3f})")
    print(f"   Ghee Amount: ₹{test_ghee_amount:.2f} (vs ₹{milk_chief_ghee_amount:.2f})")
    print(f"   Powder Amount: ₹{test_powder_amount:.2f} (vs ₹{milk_chief_powder_amount:.2f})")
    print(f"   Total Amount: ₹{test_total:.2f} (vs ₹{milk_chief_total:.2f})")
    print()
    
    # Check if Milk Chief uses different rate calculation
    # Let's work backwards from their amounts
    implied_ghee_rate = milk_chief_ghee_amount / milk_chief_ghee_kgs
    implied_powder_rate = milk_chief_powder_amount / milk_chief_powder_kgs
    
    print(f"🔍 Implied Rates from Milk Chief Amounts:")
    print(f"   Implied Ghee Rate: ₹{implied_ghee_rate:.2f}/kg (vs ₹{milk_chief_ghee_rate:.2f})")
    print(f"   Implied Powder Rate: ₹{implied_powder_rate:.2f}/kg (vs ₹{milk_chief_powder_rate:.2f})")
    print()
    
    # Calculate what 60:40 split would give with rate_per_100kg = 4850
    calc_ghee_rate = (rate_per_100kg * 0.60) / 6.5
    calc_powder_rate = (rate_per_100kg * 0.40) / 8.5
    
    print(f"🔍 Our 60:40 Split Calculation:")
    print(f"   Ghee Rate: ₹{calc_ghee_rate:.2f}/kg")
    print(f"   Powder Rate: ₹{calc_powder_rate:.2f}/kg")
    print()
    
    # Try different splits to match Milk Chief rates
    for ghee_share in [0.59, 0.595, 0.58, 0.61, 0.62]:
        ghee_rate_test = (rate_per_100kg * ghee_share) / 6.5
        snf_share = 1 - ghee_share
        powder_rate_test = (rate_per_100kg * snf_share) / 8.5
        
        diff_ghee = abs(ghee_rate_test - milk_chief_ghee_rate)
        diff_powder = abs(powder_rate_test - milk_chief_powder_rate)
        
        if diff_ghee < 0.01 and diff_powder < 0.01:
            print(f"✅ Found matching split: Ghee {ghee_share:.3f}, SNF {snf_share:.3f}")
            print(f"   Ghee Rate: ₹{ghee_rate_test:.2f} (diff: {diff_ghee:.4f})")
            print(f"   Powder Rate: ₹{powder_rate_test:.2f} (diff: {diff_powder:.4f})")

if __name__ == "__main__":
    debug_milk_chief_difference()
