-- Multi-Customer Database Migration Script
-- Execute this script to transform single-company to multi-customer system

-- 1. Create user_companies association table
CREATE TABLE IF NOT EXISTS user_companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    role VARCHAR(20) DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 2. Add is_super_admin column to users table
ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE;

-- 3. Migrate existing user-company relationships
INSERT INTO user_companies (user_id, company_id, role)
SELECT id, company_id, role FROM users WHERE company_id IS NOT NULL;

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_companies_user_id ON user_companies(user_id);
CREATE INDEX IF NOT EXISTS idx_user_companies_company_id ON user_companies(company_id);
CREATE INDEX IF NOT EXISTS idx_user_companies_active ON user_companies(is_active);

-- 5. Update existing super admin (first user)
UPDATE users SET is_super_admin = TRUE WHERE id = 1;

-- 6. Create company_access_log for audit trail
CREATE TABLE IF NOT EXISTS company_access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'login', 'logout', 'switch', 'grant', 'revoke'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 7. Create company_settings table for per-company configurations
CREATE TABLE IF NOT EXISTS company_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(20) DEFAULT 'string', -- string, number, boolean, json
    updated_by INTEGER,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(company_id, setting_key)
);

-- 8. Insert default company settings
INSERT INTO company_settings (company_id, setting_key, setting_value, setting_type) 
SELECT id, 'default_currency', 'INR', 'string' FROM companies;

INSERT INTO company_settings (company_id, setting_key, setting_value, setting_type) 
SELECT id, 'date_format', 'DD-MM-YYYY', 'string' FROM companies;

INSERT INTO company_settings (company_id, setting_key, setting_value, setting_type) 
SELECT id, 'decimal_places', '2', 'number' FROM companies;

-- 9. Create user_permissions table for granular access control
CREATE TABLE IF NOT EXISTS user_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    module VARCHAR(50) NOT NULL, -- 'invoices', 'reports', 'users', 'settings'
    permissions TEXT, -- JSON array of permissions
    granted_by INTEGER,
    granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL
);

COMMIT;
