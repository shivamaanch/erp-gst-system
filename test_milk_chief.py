# Test with Milk Chief exact formula
qty = 897  # kg
fat = 4.3  # %
clr = 29.5  # 
rate_per_100kg = 4850

# Richmond's Formula: SNF = (CLR/4) + (0.20 × Fat) + 0.14
snf = (clr / 4) + (0.20 * fat) + 0.14
snf = round(snf, 3)  # Keep 3 decimal places
print(f'SNF (Richmond Formula): {snf:.3f}%')

# Component weights with 3 decimal precision
bf_kgs = qty * fat / 100.0
snf_kgs = qty * snf / 100.0
bf_kgs = round(bf_kgs, 3)
snf_kgs = round(snf_kgs, 3)
print(f'BF Kgs: {bf_kgs:.3f}')
print(f'SNF Kgs: {snf_kgs:.3f}')

# Component rates using 60:40 split
fat_share = 0.60
snf_share = 0.40
std_fat_kg = 6.5
std_snf_kg = 8.5

bf_rate = (rate_per_100kg * fat_share) / std_fat_kg
snf_rate = (rate_per_100kg * snf_share) / std_snf_kg
print(f'BF Rate: ₹{bf_rate:.2f}/kg')
print(f'SNF Rate: ₹{snf_rate:.2f}/kg')

# Final calculation
bf_amount = bf_kgs * bf_rate
snf_amount = snf_kgs * snf_rate
total_amount = bf_amount + snf_amount
print(f'BF Amount: ₹{bf_amount:.2f}')
print(f'SNF Amount: ₹{snf_amount:.2f}')
print(f'Total Amount: ₹{total_amount:.2f}')

# Compare with Milk Chief
print(f'\nMilk Chief Expected: ₹34,403.60')
print(f'Our Calculation: ₹{total_amount:.2f}')
print(f'Difference: ₹{abs(total_amount - 34403.60):.2f}')
print(f'Match: {"✅ PERFECT" if abs(total_amount - 34403.60) < 0.01 else "❌ Different"}')

# Show component breakdown like Milk Chief
print(f'\nComponent Breakdown:')
print(f'Ghee (Fat): {bf_kgs:.3f} kg × ₹{bf_rate:.2f} = ₹{bf_amount:.2f}')
print(f'Powder (SNF): {snf_kgs:.3f} kg × ₹{snf_rate:.2f} = ₹{snf_amount:.2f}')
print(f'Total: ₹{total_amount:.2f}')
