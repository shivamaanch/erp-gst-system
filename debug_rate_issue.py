# From debug output:
# qty = 897, amount = 34413.83
# The rate shown (38.3655) seems to be amount/qty, not the actual rate

qty = 897
amount = 34413.83

# Calculate the actual rate per litre from amount
rate_per_litre = amount / qty
print(f'Rate per litre from amount: ₹{rate_per_litre:.4f}')

# Calculate what the rate per 100kg should be
rate_per_100kg = rate_per_litre * 100
print(f'Rate per 100kg should be: ₹{rate_per_100kg:.2f}')

# The issue is in the edit function - it's calculating rate as final_amount / qty
# But we want to store it as rate per 100kg, so it should be:
correct_stored_rate = rate_per_100kg
print(f'Correct stored rate should be: ₹{correct_stored_rate:.2f}')

# Let's verify with Milk Chief calculation
daily_rate = 4850  # This is rate per 100kg
qty = 897
fat = 4.3
clr = 29.5

# Richmond's formula with Milk Chief adjustment
snf = (clr / 4) + (0.20 * fat) + 0.14
snf = round(snf, 3) - 0.005
snf = round(snf, 3)
print(f'SNF: {snf:.3f}%')

# Component weights
bf_kgs = qty * fat / 100.0
snf_kgs = qty * snf / 100.0
bf_kgs = round(bf_kgs, 3)
snf_kgs = round(snf_kgs, 3)
print(f'BF Kgs: {bf_kgs:.3f}')
print(f'SNF Kgs: {snf_kgs:.3f}')

# Component rates (60:40 split)
fat_share = 0.60
snf_share = 0.40
std_fat_kg = 6.5
std_snf_kg = 8.5

bf_rate = (daily_rate * fat_share) / std_fat_kg
snf_rate = (daily_rate * snf_share) / std_snf_kg
print(f'BF Rate: ₹{bf_rate:.2f}/kg')
print(f'SNF Rate: ₹{snf_rate:.2f}/kg')

# Final calculation
bf_amount = bf_kgs * bf_rate
snf_amount = snf_kgs * snf_rate
final_amount = bf_amount + snf_amount
print(f'Final Amount: ₹{final_amount:.2f}')

# Store rate per 100kg
stored_rate = daily_rate  # This should be stored as rate per 100kg
print(f'Should store rate as: ₹{stored_rate:.2f} (per 100kg)')
