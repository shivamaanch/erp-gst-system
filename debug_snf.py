# Let's try different SNF precision approaches
qty = 897  # kg
fat = 4.3  # %
clr = 29.5  # 
rate_per_100kg = 4850

# Richmond's Formula: SNF = (CLR/4) + (0.20 × Fat) + 0.14
snf_exact = (clr / 4) + (0.20 * fat) + 0.14
print(f'SNF Exact: {snf_exact:.6f}%')

# Try different rounding approaches
snf_3dp = round(snf_exact, 3)
snf_2dp = round(snf_exact, 2)
snf_no_round = snf_exact

print(f'SNF 3 decimal: {snf_3dp:.3f}%')
print(f'SNF 2 decimal: {snf_2dp:.2f}%')
print(f'SNF no round: {snf_no_round:.6f}%')

# Calculate SNF Kgs with different approaches
for name, snf_val in [("Exact", snf_no_round), ("3dp", snf_3dp), ("2dp", snf_2dp)]:
    snf_kgs = qty * snf_val / 100.0
    snf_kgs_rounded = round(snf_kgs, 3)
    print(f'{name} SNF Kgs: {snf_kgs_rounded:.3f}')

# Milk Chief shows 75.079 kg, let's work backwards
target_snf_kgs = 75.079
target_snf_percent = (target_snf_kgs / qty) * 100
print(f'\nTarget SNF % from Milk Chief: {target_snf_percent:.6f}%')
print(f'Difference from our SNF: {abs(target_snf_percent - snf_exact):.6f}%')

# Maybe Milk Chief uses different rounding in intermediate steps?
# Let's try unrounded SNF calculation
snf_kgs_unrounded = qty * snf_exact / 100.0
print(f'Unrounded SNF Kgs: {snf_kgs_unrounded:.6f}')

# Try rounding only at final step
bf_kgs = qty * fat / 100.0
bf_kgs = round(bf_kgs, 3)  # 38.571

# Component rates
fat_share = 0.60
snf_share = 0.40
std_fat_kg = 6.5
std_snf_kg = 8.5

bf_rate = (rate_per_100kg * fat_share) / std_fat_kg
snf_rate = (rate_per_100kg * snf_share) / std_snf_kg

# Try with unrounded SNF Kgs
bf_amount = bf_kgs * bf_rate
snf_amount_unrounded = snf_kgs_unrounded * snf_rate
total_unrounded = bf_amount + snf_amount_unrounded

print(f'\nWith unrounded SNF Kgs:')
print(f'BF Amount: ₹{bf_amount:.2f}')
print(f'SNF Amount (unrounded): ₹{snf_amount_unrounded:.2f}')
print(f'Total (unrounded): ₹{total_unrounded:.2f}')

# Try with Milk Chief target SNF Kgs
snf_amount_target = target_snf_kgs * snf_rate
total_target = bf_amount + snf_amount_target

print(f'\nWith Milk Chief target SNF Kgs:')
print(f'SNF Amount (target): ₹{snf_amount_target:.2f}')
print(f'Total (target): ₹{total_target:.2f}')
print(f'Match with Milk Chief: {"✅" if abs(total_target - 34403.60) < 0.01 else "❌"}')
