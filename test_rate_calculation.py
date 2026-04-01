# Test the current rate calculation
# Based on the debug output: qty=897, rate=38.3655, amount=34413.83

qty = 897
rate_per_100kg = 38.3655  # This should be stored as rate per 100kg
amount = 34413.83

# Calculate what the rate per litre would be
rate_per_litre = rate_per_100kg / 100
print(f'Rate per 100kg: ₹{rate_per_100kg:.2f}')
print(f'Rate per litre: ₹{rate_per_litre:.4f}')

# Calculate amount using rate per litre
calculated_amount_litre = qty * rate_per_litre
print(f'Amount using rate per litre: ₹{calculated_amount_litre:.2f}')

# Calculate amount using rate per 100kg
calculated_amount_100kg = qty * (rate_per_100kg / 100)
print(f'Amount using rate per 100kg: ₹{calculated_amount_100kg:.2f}')

print(f'Expected amount: ₹{amount:.2f}')
print(f'Difference: ₹{abs(calculated_amount_100kg - amount):.2f}')

# The issue is that the rate is still being stored as rate per litre
# Let's calculate what it should be as rate per 100kg
correct_rate_per_100kg = (amount / qty) * 100
print(f'Correct rate per 100kg should be: ₹{correct_rate_per_100kg:.2f}')
