# 🚀 NORTHFLANK DEPLOYMENT GUIDE

## 🎯 TEMPORARY LOGIN BYPASS FOR DEPLOYMENT

### **Problem:**
Unable to login on Northflank deployment - need temporary bypass for testing.

### **Solution:**
Added temporary login bypass that auto-logs in as the first user.

## 📋 DEPLOYMENT STEPS

### **1. Environment Variables**
Set this environment variable in Northflank:
```
DISABLE_LOGIN=true
```

### **2. Access Methods**

**Method 1: Direct Access**
- Go to: `https://your-app-url.northflank.com/`
- Will auto-login as first user
- Redirect to reports hub

**Method 2: Bypass Route**
- Go to: `https://your-app-url.northflank.com/bypass`
- Force auto-login and redirect to hub

**Method 3: Normal Login**
- Go to: `https://your-app-url.northflank.com/login`
- If DISABLE_LOGIN=true, will auto-login
- If DISABLE_LOGIN=false, normal login required

## 🔧 HOW IT WORKS

### **Auto-Login Process:**
1. System checks if user is authenticated
2. If not, and DISABLE_LOGIN=true, auto-logs in as first user
3. Sets up session with first company
4. Redirects to reports hub

### **Session Setup:**
- **User:** First user in database (usually admin)
- **Company:** First company in database
- **Role:** Admin
- **Financial Year:** Active financial year or "2025-26"

## 📊 FEATURES AVAILABLE

### **Multi-Customer System:**
- ✅ Company switching in topbar
- ✅ Multi-company user access
- ✅ Role-based access control
- ✅ Super admin capabilities

### **Milk Business System:**
- ✅ Milk collection invoices
- ✅ Milk statement reports
- ✅ Quality tracking (Fat %, SNF %)
- ✅ Date filtering with current month default

### **Enhanced Reporting:**
- ✅ Profit & Loss statements
- ✅ Balance Sheets
- ✅ Trial Balance
- ✅ GST Reports (GSTR1, GSTR2B, GSTR3B)
- ✅ TDS/TCS Reports

## 🛠️ TECHNICAL DETAILS

### **Login Bypass Code:**
```python
# In app.py
app.config["DISABLE_LOGIN"] = os.getenv("DISABLE_LOGIN", "false").lower() == "true"

@login_manager.unauthorized_handler
def unauthorized():
    if app.config.get('DISABLE_LOGIN', False):
        # Auto-login as first user
        user = User.query.first()
        if user:
            login_user(user)
            # Set up session
            return redirect(url_for("reports.hub"))
    return redirect(url_for("auth.login"))
```

### **Bypass Route:**
```python
@app.route("/bypass")
def bypass_login():
    """TEMPORARY: Direct access for Northflank testing"""
    # Auto-login and redirect to hub
```

## 📝 TESTING CHECKLIST

### **After Deployment:**
- [ ] Access main URL (`/`) - should auto-login
- [ ] Access bypass route (`/bypass`) - should auto-login
- [ ] Check company switcher in topbar
- [ ] Test milk business features
- [ ] Verify all reports work
- [ ] Check multi-customer functionality

### **Expected Behavior:**
- ✅ No login prompt
- ✅ Direct access to reports hub
- ✅ Company name displayed in topbar
- ✅ All menu items accessible
- ✅ Reports generate correctly

## 🔒 SECURITY NOTE

### **⚠️ IMPORTANT:**
This is a **temporary bypass** for deployment testing only.

### **For Production:**
1. Set `DISABLE_LOGIN=false` in environment
2. Remove bypass routes after testing
3. Set up proper user authentication
4. Configure secure login credentials

### **Recommended Timeline:**
- **Testing Phase:** Keep bypass enabled
- **Production Launch:** Disable bypass
- **Post-Launch:** Remove bypass code

## 🚀 DEPLOYMENT COMMANDS

### **Northflank Setup:**
```bash
# Environment Variables
DISABLE_LOGIN=true
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
```

### **Database Migration:**
```bash
# Run migration on Northflank
python run_essential_migration.py
```

### **Verification:**
```bash
# Test auto-login
curl -I https://your-app-url.northflank.com/
# Should return 302 redirect to reports hub
```

## 📞 TROUBLESHOOTING

### **Common Issues:**

**Issue 1: Still showing login page**
- Check DISABLE_LOGIN environment variable
- Verify app restart after setting variable
- Check logs for errors

**Issue 2: No user in database**
- Run database migration first
- Ensure at least one user exists
- Check database connection

**Issue 3: Company switcher not working**
- Verify user has company access
- Check user_companies table
- Ensure company data exists

**Issue 4: Reports not loading**
- Check financial year setup
- Verify account data exists
- Check database schema

## 🎯 NEXT STEPS

### **Immediate:**
1. Deploy with DISABLE_LOGIN=true
2. Test all features thoroughly
3. Verify multi-customer functionality
4. Test milk business system

### **Short-term:**
1. Set up proper user accounts
2. Configure secure authentication
3. Test normal login flow
4. Prepare for production launch

### **Long-term:**
1. Remove bypass code
2. Implement proper security
3. Set up user management
4. Configure role-based access

---

## 🎉 DEPLOYMENT SUCCESS!

**Your multi-customer ERP system is ready for Northflank deployment with temporary login bypass!** 🚀

### **Quick Start:**
1. Set `DISABLE_LOGIN=true` in Northflank
2. Deploy your application
3. Access URL - auto-login enabled
4. Test all multi-customer features
5. Test milk business system

### **After Testing:**
1. Set `DISABLE_LOGIN=false`
2. Configure proper authentication
3. Remove bypass code if needed
4. Launch for production use

---

**Ready for Northflank deployment with temporary login bypass!** 🎯
