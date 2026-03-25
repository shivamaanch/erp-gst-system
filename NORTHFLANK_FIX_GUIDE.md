# 🔧 NORTHFLANK DEPLOYMENT FIX

## 🚨 PROBLEM IDENTIFIED

**Error:** `column users.is_super_admin does not exist`

**Cause:** Database migration hasn't been run on Northflank PostgreSQL database.

## ✅ SOLUTION: RUN MIGRATION

### **Step 1: Access Northflank Shell**
1. Go to your Northflank service
2. Click **"Shell (SSH)"**
3. This will open a terminal in your running container

### **Step 2: Run Quick Migration**
Copy and paste this command in the shell:

```bash
python quick_migration.py
```

### **Alternative: Full Migration**
If the quick migration doesn't work, try:

```bash
python northflank_migration.py
```

### **Step 3: Restart Service**
After migration completes:
1. Go to **Deployments** tab
2. Click **"Redeploy"** or **Restart**
3. Wait for the service to restart

### **Step 4: Test Application**
1. Go to your service URL
2. Should auto-login now
3. Test multi-customer features

## 📋 EXPECTED OUTPUT

### **Quick Migration Success:**
```
🔄 Starting quick migration...
✅ Created all tables
✅ Added is_super_admin column
✅ Updated first user to super admin
✅ Migrated user-company relationships
🎉 Migration completed successfully!

📊 Database Summary:
  Users: 1
  Companies: 1
  User-Company Relationships: 1
```

### **If Migration Fails:**
```
❌ Migration failed: [error message]
```

Check:
- DATABASE_URL environment variable
- Database connection
- Database permissions

## 🔧 TROUBLESHOOTING

### **Issue 1: Python not found**
```bash
# Try these commands:
python3 quick_migration.py
# or
python quick_migration.py
```

### **Issue 2: Module not found**
```bash
# Install required packages
pip install psycopg2-binary
# then run migration again
```

### **Issue 3: Database connection error**
```bash
# Check environment variables
echo $DATABASE_URL
# Should show: postgresql://username:password@host:port/database
```

### **Issue 4: Permission denied**
```bash
# Check if database user has ALTER permissions
# Contact Northflank support if needed
```

## 🚀 ALTERNATIVE APPROACH

### **If Shell Access Doesn't Work:**

1. **Add Migration to App Startup:**
   - Add migration code to app.py
   - Run migration on first startup
   - Remove after successful migration

2. **Use Northflank Jobs:**
   - Create a one-time job
   - Run migration script
   - Delete job after completion

3. **Local Migration & Deploy:**
   - Run migration locally
   - Export database
   - Import to Northflank
   - Deploy updated code

## 📊 MIGRATION DETAILS

### **What the Migration Does:**

1. **Adds Missing Column:**
   ```sql
   ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE
   ```

2. **Creates Tables:**
   ```sql
   CREATE TABLE user_companies (
       id SERIAL PRIMARY KEY,
       user_id INTEGER REFERENCES users(id),
       company_id INTEGER REFERENCES companies(id),
       role VARCHAR(20) DEFAULT 'viewer',
       is_active BOOLEAN DEFAULT TRUE,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   
   CREATE TABLE company_access_log (
       id SERIAL PRIMARY KEY,
       user_id INTEGER REFERENCES users(id),
       company_id INTEGER REFERENCES companies(id),
       action VARCHAR(50) NOT NULL,
       timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       ip_address VARCHAR(45),
       user_agent TEXT
   );
   ```

3. **Migrates Data:**
   ```sql
   INSERT INTO user_companies (user_id, company_id, role)
   SELECT id, company_id, role FROM users WHERE company_id IS NOT NULL;
   ```

4. **Sets Up Super Admin:**
   ```sql
   UPDATE users SET is_super_admin = TRUE WHERE id = 1;
   ```

## 🎯 SUCCESS INDICATORS

### **After Successful Migration:**
- ✅ Application starts without database errors
- ✅ Auto-login works (with DISABLE_LOGIN=true)
- ✅ Multi-customer features available
- ✅ Company switcher visible in topbar
- ✅ All reports accessible

### **Database Should Have:**
- ✅ `users.is_super_admin` column
- ✅ `user_companies` table
- ✅ `company_access_log` table
- ✅ Proper indexes
- ✅ Migrated user-company relationships

## 📞 NEXT STEPS

### **After Migration Success:**
1. **Test All Features:**
   - Company switching
   - Milk business system
   - Report generation
   - User management

2. **Set Up Proper Authentication:**
   - Create user accounts
   - Set strong passwords
   - Configure roles
   - Test normal login

3. **Remove Temporary Bypass:**
   - Set DISABLE_LOGIN=false
   - Remove bypass routes
   - Test normal login flow

4. **Go Live:**
   - System ready for production
   - Multi-customer functionality working
   - All business features available

---

## 🎉 EXPECTED RESULT

**After running the migration, your Northflank deployment should work perfectly!** 🚀

### **You'll Have:**
- ✅ Working multi-customer ERP system
- ✅ Auto-login for testing
- ✅ Complete milk business support
- ✅ Professional reporting
- ✅ Data isolation between companies

### **Ready For:**
- 🏢 Multi-client management
- 🥛 Dairy business operations
- 📊 Professional reporting
- 👥 User management
- 🔒 Secure data handling

---

**Run the migration in Northflank shell and your system will be working!** 🎯
