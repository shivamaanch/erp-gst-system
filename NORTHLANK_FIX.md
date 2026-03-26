# NORTHFLANK FIX INSTRUCTIONS

## SSH into container:
ssh p01--accts--gzfb6r9tnqwp.code.run

## Run fix:
cd /app
git pull origin main
python northflank_fix.py

## Expected output:
Starting Northflank fix...
Added voucher_no to bills
Added voucher_no to milk_transactions
Created bills.voucher_no index
Created milk_transactions.voucher_no index
Fix completed! Application should start now.

## If script fails, run manual SQL:
ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50);
ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50);

## After fix:
- Application should start without errors
- Build should complete successfully
- All features should work
