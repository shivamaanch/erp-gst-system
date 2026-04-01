# Your example data
qty = 897  # kg
fat = 4.3  # %
clr = 29.5  # after conversion from 295
rate_per_100kg = 4850

# Bihar SNF formula: SNF = (CLR/4) + (0.20 × Fat) + 0.14
snf = (clr / 4) + (0.20 * fat) + 0.14
print(f'SNF calculated: {snf:.2f}%')

# Component weights
bf_kgs = qty * fat / 100.0
snf_kgs = qty * snf / 100.0
print(f'BF Kgs: {bf_kgs:.2f}')
print(f'SNF Kgs: {snf_kgs:.2f}')

# Current system calculation (60:40 split)
fat_share = 0.60
snf_share = 0.40
std_fat_kg = 6.5
std_snf_kg = 8.5

bf_rate = (rate_per_100kg * fat_share) / std_fat_kg
snf_rate = (rate_per_100kg * snf_share) / std_snf_kg
print(f'BF Rate: ₹{bf_rate:.2f}/kg')
print(f'SNF Rate: ₹{snf_rate:.2f}/kg')

amount_current = bf_kgs * bf_rate + snf_kgs * snf_rate
print(f'Current System Amount: ₹{amount_current:.2f}')

# Your expected amount
print(f'Your Expected Amount: ₹34403.60')
print(f'Difference: ₹{amount_current - 34403.60:.2f}')

# Alternative calculation - maybe you use different formula?
# Let's try direct rate per kg based on actual composition
total_solids = bf_kgs + snf_kgs
rate_per_kg_solids = rate_per_100kg / 100.0  # Convert per 100kg to per kg
amount_alt = total_solids * rate_per_kg_solids
print(f'Alternative Amount (direct solids): ₹{amount_alt:.2f}')

# Another approach - maybe you use different split?
# Let's try 70:30 split
bf_rate_70 = (rate_per_100kg * 0.70) / std_fat_kg
snf_rate_70 = (rate_per_100kg * 0.30) / std_snf_kg
amount_70 = bf_kgs * bf_rate_70 + snf_kgs * snf_rate_70
print(f'70:30 Split Amount: ₹{amount_70:.2f}')

# Maybe you use actual fat/snf ratio for split?
actual_fat_ratio = bf_kgs / (bf_kgs + snf_kgs)
actual_snf_ratio = snf_kgs / (bf_kgs + snf_kgs)
bf_rate_actual = (rate_per_100kg * actual_fat_ratio) / std_fat_kg
snf_rate_actual = (rate_per_100kg * actual_snf_ratio) / std_snf_kg
amount_actual = bf_kgs * bf_rate_actual + snf_kgs * snf_rate_actual
print(f'Actual Ratio Split Amount: ₹{amount_actual:.2f}')
print(f'Actual Fat Ratio: {actual_fat_ratio:.3f}, SNF Ratio: {actual_snf_ratio:.3f}')
