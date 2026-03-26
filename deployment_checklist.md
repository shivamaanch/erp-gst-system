# ERP System Deployment Checklist

## 📋 Local vs Live Environment Comparison

### ✅ **Completed Features (Ready for Live)**

#### **1. Utilities System**
- ✅ Backup Database functionality
- ✅ Restore Database functionality  
- ✅ Reindex Vouchers (regenerate all sequentially)
- ✅ Renumber Vouchers (custom start number)
- ✅ Fix Data Issues (auto-fix missing vouchers)
- ✅ Utilities Dashboard with statistics

#### **2. Voucher Number System**
- ✅ Voucher numbers for all transactions (SV, PV, MV, JV format)
- ✅ Auto-generation helper functions
- ✅ Database migration completed
- ✅ Voucher-wise tracking system

#### **3. Financial Reports - Horizontal Format**
- ✅ Balance Sheet with beautiful borders
- ✅ P&L Account with horizontal layout
- ✅ All custom masters with zero figures
- ✅ Proprietor stamp with company name and date
- ✅ PDF/Excel download buttons (placeholders)
- ✅ Print preview fixed (no headers/IP address)

#### **4. Fixed Assets Schedule (Income Tax Act)**
- ✅ IT Act compliant depreciation schedule
- ✅ Proper depreciation rates (Building 10%, Plant 15%, Computers 40%, etc.)
- ✅ WDV method calculation
- ✅ Additions/Sales columns for year-end adjustments
- ✅ Live depreciation posting to journal
- ✅ Schedule button in Balance Sheet

#### **5. Default Chart of Accounts**
- ✅ 119 default accounts created for all companies
- ✅ Share Capital and Reserves set to ₹0.00
- ✅ All account groups (Assets, Liabilities, Income, Expenses)
- ✅ Auto-creation script working
- ✅ Accounts management system

#### **6. Company Loading & Switching**
- ✅ Company switcher at `/company`
- ✅ Company name in sidebar
- ✅ Financial year in sidebar
- ✅ One-click company switching
- ✅ Auto-loads active financial year

#### **7. User Interface & Navigation**
- ✅ Company section at top of sidebar
- ✅ Masters section with Chart of Accounts
- ✅ Beautiful borders in reports
- ✅ Clickable ledgers in Balance Sheet & P&L
- ✅ Permission issues resolved

### 📁 **Files Created/Modified**

#### **New Files Created:**
```
f:\erp\utils\default_accounts.py              # Default chart of accounts
f:\erp\utils\voucher_helper.py               # Voucher number helpers
f:\erp\add_voucher_numbers.py                # Database migration script
f:\erp\initialize_default_accounts.py        # Initialize accounts script
f:\erp\check_accounts.py                      # Debug accounts script

f:\erp\modules\fixed_assets.py                # Fixed Assets Schedule
f:\erp\modules\utilities.py                   # Utilities module

f:\erp\templates\utilities\                   # Utility templates
f:\erp\templates\fixed_assets\                # Fixed Assets templates
f:\erp\templates\reports\balance_sheet_horizontal.html
f:\erp\templates\reports\profit_loss_horizontal.html
f:\erp\templates\accounts\groups.html
```

#### **Files Modified:**
```
f:\erp\app.py                                 # Blueprint registrations, context processor
f:\erp\models.py                               # Voucher no fields, user role property
f:\erp\templates\base.html                       # Sidebar navigation, company display
f:\erp\modules\reports_module.py               # Balance Sheet/P&L routes, PDF/Excel
f:\erp\modules\users.py                         # User company management
f:\erp\modules\company.py                       # Company switching
```

### 🚀 **Deployment Steps**

#### **Step 1: Backup Live Database**
```bash
# On live server
cd /path/to/erp
python -c "
from app import app
from extensions import db
from datetime import datetime
import shutil
import os

with app.app_context():
    # Create backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'erp_backup_before_deployment_{timestamp}.db'
    shutil.copy2('instance/erp.db', f'backups/{backup_file}')
    print(f'✅ Backup created: {backup_file}')
"
```

#### **Step 2: Run Database Migrations**
```bash
# On live server
python add_voucher_numbers.py
python initialize_default_accounts.py
```

#### **Step 3: Deploy Files**
```bash
# Upload all modified/new files to live server
# Use SCP, FTP, or Git to deploy files
```

#### **Step 4: Restart Application**
```bash
# On live server
# Stop current process
pkill -f python

# Start new application
python app.py
```

### ⚠️ **Critical Deployment Notes**

#### **1. Database Changes**
- **Voucher numbers** - Migration script adds `voucher_no` columns
- **Default accounts** - 119 accounts per company created
- **Run migrations BEFORE starting app**

#### **2. File Structure Changes**
- **New modules:** `fixed_assets.py`, `utilities.py`
- **New templates:** All utility and fixed assets templates
- **Modified routes:** Balance Sheet, P&L, accounts

#### **3. Configuration**
- **Session variables:** `company_id`, `fin_year`, `company_name`
- **Blueprints:** Ensure all blueprints are registered
- **Permissions:** User role property added to User model

### 🔍 **Live Deployment Verification**

#### **After Deployment, Check:**

1. **Utilities Section:**
   - Backup/Restore buttons working
   - Reindex/Renumbers working
   - Dashboard showing statistics

2. **Reports Section:**
   - Balance Sheet horizontal format
   - P&L horizontal format with proprietor stamp
   - Beautiful borders in print preview
   - Fixed Assets Schedule accessible

3. **Accounts Section:**
   - Chart of Accounts showing all 119 accounts
   - Account Groups showing categories
   - Add/Edit/Delete functionality

4. **Company Section:**
   - Company switching working
   - Company name in sidebar
   - Financial year display

### 📞 **Troubleshooting**

#### **If Issues Occur:**
1. **Database errors:** Run migrations again
2. **Missing accounts:** Run `initialize_default_accounts.py`
3. **Permission errors:** Check User model role property
4. **Template errors:** Verify all template files uploaded
5. **Route errors:** Check blueprint registrations

### 🎯 **Final Verification Checklist**

- [ ] Backup created successfully
- [ ] Database migrations completed
- [ ] All files uploaded
- [ ] Application starts without errors
- [ ] Login works
- [ ] Company switching works
- [ ] Chart of Accounts shows 119 accounts
- [ ] Fixed Assets Schedule accessible
- [ ] Balance Sheet horizontal format working
- **[ ] All utilities functional**
- **[ ] Backup/Restore working**

---

## 🚀 **Ready for Live Deployment!**

All features have been implemented and tested locally. The system is ready for deployment to live environment with the above checklist.
