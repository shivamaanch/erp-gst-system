# NORTHFLANK DATABASE FIX INSTRUCTIONS

## PROBLEM
Live database missing voucher_no columns causing build errors.

## SOLUTION
SSH into Northflank container and run database fix.

## STEPS

### 1. SSH into Container
```bash
ssh p01--accts--gzfb6r9tnqwp.code.run
```

### 2. Run Database Fix
```bash
cd /app
python live_db_fix.py
```

### 3. Restart Application (if needed)
```bash
# Application should auto-restart
# If not, restart through Northflank dashboard
```

## EXPECTED OUTPUT
```
Starting database fix...
Added voucher_no to bills table
Added voucher_no to milk_transactions table
Database fix completed!
```

## VERIFICATION
After fix:
- Check Northflank logs
- Application should start without database errors
- Build should complete successfully

## ALTERNATIVE METHOD
If SSH doesn't work:
1. Use Northflank "Shell (SSH)" in dashboard
2. Navigate to /app directory
3. Run the fix script
4. Monitor logs for success

## TROUBLESHOOTING
If fix fails:
- Check database permissions
- Verify PostgreSQL connection
- Check Northflank logs for detailed errors
- Contact support if needed
