
# LIVE ENVIRONMENT VERIFICATION CHECKLIST
Generated: 2026-03-26 16:08:05

## BEFORE DEPLOYMENT
- [ ] Local verification passed (100% OK)
- [ ] Database backup created
- [ ] All migrations tested locally

## AFTER DEPLOYMENT - CRITICAL CHECKS

### 1. File Verification
Check these files exist on live server:
- [ ] app.py
- [ ] models.py
- [ ] modules/fixed_assets.py
- [ ] modules/utilities.py
- [ ] modules/accounts.py
- [ ] templates/reports/balance_sheet_horizontal.html
- [ ] templates/fixed_assets/schedule_it_act.html
- [ ] templates/utilities/backup_database.html

### 2. Database Verification
- [ ] All tables exist (users, companies, accounts, bills, milk_transactions)
- [ ] voucher_no columns exist in bills and milk_transactions tables
- [ ] Default accounts created (50+ per company)
- [ ] Voucher numbers populated for existing records

### 3. Feature Verification
- [ ] Login works
- [ ] Company switching works
- [ ] Chart of Accounts shows all default accounts
- [ ] Fixed Assets Schedule accessible
- [ ] Utilities (Backup/Restore/Reindex/Renumber) working
- [ ] Balance Sheet horizontal format with borders
- [ ] P&L horizontal format with proprietor stamp
- [ ] Fixed Assets Schedule (IT Act format) working
- [ ] Depreciation posting working

### 4. UI Verification
- [ ] Company section at top of sidebar
- [ ] Masters section with Chart of Accounts
- [ ] Beautiful borders in reports
- [ ] Print preview fixed (no headers)
- [ ] Clickable ledgers working

### 5. Performance Verification
- [ ] Application starts without errors
- [ ] Pages load quickly
- [ ] Database queries working
- [ ] No error logs

## FINAL VERIFICATION
- [ ] All 119 default accounts present per company
- [ ] Share Capital and Reserves at 0.00
- [ ] Voucher numbers in SV/PV/MV/JV format
- [ ] All utilities functional
- [ ] Reports displaying correctly

## SIGNOFF
- [ ] Local environment: 100% verified
- [ ] Live deployment: 100% verified
- [ ] All features working: Confirmed
- [ ] Ready for production: YES

## TROUBLESHOOTING
If any check fails:
1. Check file permissions
2. Verify database migrations ran
3. Check application logs
4. Re-run failed migration scripts
5. Contact support if needed
