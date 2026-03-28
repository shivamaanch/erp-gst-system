# app.py
from flask import Flask, redirect, url_for, session
from flask_login import current_user
from extensions import db, login_manager, migrate
from dotenv import load_dotenv
import os

load_dotenv()

def run_database_migration():
    """Run database migration before app initialization"""
    import psycopg2
    import urllib.parse
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found!")
        return False
    
    try:
        parsed = urllib.parse.urlparse(db_url)
        
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
        
        cursor = conn.cursor()
        print("[REFRESH] Running comprehensive database migration...")
        
        # 1. Fix users table
        try:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'is_super_admin'
            """)
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE")
                print("Added is_super_admin column to users")
        except Exception as e:
            print(f"Warning: is_super_admin column issue: {e}")
        
        # 1.5. Fix companies table - add missing columns
        companies_columns = [
            ("business_type", "VARCHAR(50) DEFAULT 'service'"),
            ("gstin", "VARCHAR(15)"),
            ("pan", "VARCHAR(10)"),
            ("state_code", "VARCHAR(2)"),
            ("address", "TEXT"),
            ("phone", "VARCHAR(15)"),
            ("email", "VARCHAR(100)"),
            ("logo_path", "VARCHAR(255)"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        
        for col_name, col_type in companies_columns:
            try:
                cursor.execute(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'companies' AND column_name = '{col_name}'
                """)
                if not cursor.fetchone():
                    cursor.execute(f"ALTER TABLE companies ADD COLUMN {col_name} {col_type}")
                    print(f"[OK] Added {col_name} column to companies")
            except Exception as e:
                print(f"[WARNING]  {col_name} column issue: {e}")
        
        # 2. Fix bills table - add missing columns
        bills_columns = [
            ("tds_rate", "DECIMAL(5,2) DEFAULT 0.00"),
            ("tds_amount", "DECIMAL(12,2) DEFAULT 0.00"),
            ("tcs_rate", "DECIMAL(5,2) DEFAULT 0.00"),
            ("tcs_amount", "DECIMAL(12,2) DEFAULT 0.00"),
            ("template_type", "VARCHAR(50) DEFAULT 'standard'"),
            ("is_cancelled", "BOOLEAN DEFAULT FALSE"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("created_by", "INTEGER")
        ]
        
        for col_name, col_type in bills_columns:
            try:
                cursor.execute(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'bills' AND column_name = '{col_name}'
                """)
                if not cursor.fetchone():
                    cursor.execute(f"ALTER TABLE bills ADD COLUMN {col_name} {col_type}")
                    print(f"[OK] Added {col_name} column to bills")
            except Exception as e:
                print(f"[WARNING]  {col_name} column issue: {e}")
        
        # 3. Create user_companies table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_companies (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                    role VARCHAR(20) DEFAULT 'viewer',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("[OK] Created user_companies table")
        except Exception as e:
            print(f"[WARNING]  Error creating user_companies: {e}")
        
        # 4. Create company_access_log table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_access_log (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                    action VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    user_agent TEXT
                )
            """)
            print("[OK] Created company_access_log table")
        except Exception as e:
            print(f"[WARNING]  Error creating company_access_log: {e}")
        
        # 5. Create ALL missing tables if they don't exist
        tables_to_create = {
            "gst_returns": """
                CREATE TABLE IF NOT EXISTS gst_returns (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    return_type VARCHAR(20),
                    period VARCHAR(10),
                    fin_year VARCHAR(10),
                    status VARCHAR(20) DEFAULT 'pending',
                    filed_at DATE,
                    arn VARCHAR(50),
                    total_tax DECIMAL(14,2) DEFAULT 0.00,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "tds_returns": """
                CREATE TABLE IF NOT EXISTS tds_returns (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    fin_year VARCHAR(10) NOT NULL,
                    quarter VARCHAR(5),
                    form_type VARCHAR(10) DEFAULT '26Q',
                    status VARCHAR(20) DEFAULT 'Pending',
                    filed_on DATE,
                    total_tds DECIMAL(14,2) DEFAULT 0.00,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "alerts": """
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    alert_type VARCHAR(30),
                    severity VARCHAR(10) DEFAULT 'info',
                    title VARCHAR(100),
                    message TEXT,
                    is_read BOOLEAN DEFAULT FALSE,
                    due_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "loan_applications": """
                CREATE TABLE IF NOT EXISTS loan_applications (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    applicant_name VARCHAR(100) NOT NULL,
                    business_name VARCHAR(150),
                    loan_amount DECIMAL(14,2) NOT NULL,
                    loan_purpose VARCHAR(100),
                    tenure_months INTEGER,
                    existing_loans DECIMAL(14,2) DEFAULT 0.00,
                    collateral_details TEXT,
                    projected_turnover DECIMAL(14,2) DEFAULT 0.00,
                    projected_profit DECIMAL(14,2) DEFAULT 0.00,
                    status VARCHAR(20) DEFAULT 'Pending',
                    created_date DATE DEFAULT CURRENT_DATE,
                    remarks TEXT
                )
            """,
            "milk_rate_charts": """
                CREATE TABLE IF NOT EXISTS milk_rate_charts (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    chart_name VARCHAR(100) NOT NULL,
                    effective_date DATE NOT NULL,
                    fat_rate DECIMAL(8,4) NOT NULL,
                    snf_rate DECIMAL(8,4) NOT NULL,
                    base_fat DECIMAL(5,2) DEFAULT 0.00,
                    base_snf DECIMAL(5,2) DEFAULT 0.00,
                    txn_type VARCHAR(20) DEFAULT 'Both',
                    is_active BOOLEAN DEFAULT TRUE
                )
            """,
            "milk_transactions": """
                CREATE TABLE IF NOT EXISTS milk_transactions (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    fin_year VARCHAR(10) NOT NULL,
                    party_id INTEGER NOT NULL REFERENCES parties(id),
                    txn_date DATE NOT NULL,
                    shift VARCHAR(10) DEFAULT 'Morning',
                    txn_type VARCHAR(20) NOT NULL,
                    qty_liters DECIMAL(10,2) NOT NULL,
                    fat DECIMAL(5,2) NOT NULL,
                    snf DECIMAL(5,2) NOT NULL,
                    rate DECIMAL(10,4) NOT NULL,
                    amount DECIMAL(14,2) NOT NULL,
                    chart_id INTEGER REFERENCES milk_rate_charts(id),
                    narration TEXT
                )
            """,
            "purchase_invoices": """
                CREATE TABLE IF NOT EXISTS purchase_invoices (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    fin_year VARCHAR(10) NOT NULL,
                    invoice_no VARCHAR(50) NOT NULL UNIQUE,
                    invoice_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    party_id INTEGER NOT NULL REFERENCES parties(id),
                    item_name VARCHAR(100),
                    qty_liters DECIMAL(10,2),
                    fat_percent DECIMAL(5,2),
                    clr_percent DECIMAL(5,2),
                    rate_per_liter DECIMAL(10,2),
                    snf_percent DECIMAL(5,2),
                    fat_rate DECIMAL(10,2),
                    snf_rate DECIMAL(10,2),
                    fat_kgs DECIMAL(10,2),
                    snf_kgs DECIMAL(10,2),
                    taxable_amount DECIMAL(14,2),
                    gst_rate DECIMAL(5,2) DEFAULT 0.00,
                    gst_amount DECIMAL(14,2),
                    total_amount DECIMAL(14,2),
                    narration TEXT,
                    is_cancelled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "sale_invoices": """
                CREATE TABLE IF NOT EXISTS sale_invoices (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    fin_year VARCHAR(10) NOT NULL,
                    invoice_no VARCHAR(50) NOT NULL UNIQUE,
                    invoice_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    party_id INTEGER NOT NULL REFERENCES parties(id),
                    item_name VARCHAR(100),
                    qty_liters DECIMAL(10,2),
                    fat_percent DECIMAL(5,2),
                    clr_percent DECIMAL(5,2),
                    rate_per_liter DECIMAL(10,2),
                    snf_percent DECIMAL(5,2),
                    fat_rate DECIMAL(10,2),
                    snf_rate DECIMAL(10,2),
                    fat_kgs DECIMAL(10,2),
                    snf_kgs DECIMAL(10,2),
                    taxable_amount DECIMAL(14,2),
                    gst_rate DECIMAL(5,2) DEFAULT 0.00,
                    gst_amount DECIMAL(14,2),
                    total_amount DECIMAL(14,2),
                    narration TEXT,
                    is_cancelled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "bank_accounts": """
                CREATE TABLE IF NOT EXISTS bank_accounts (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    account_name VARCHAR(150) NOT NULL,
                    bank_name VARCHAR(100),
                    account_no VARCHAR(50),
                    ifsc VARCHAR(20),
                    branch VARCHAR(100),
                    account_type VARCHAR(30) DEFAULT 'Current',
                    opening_balance DECIMAL(14,2) DEFAULT 0.00,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, account_no)
                )
            """,
            "bank_transactions": """
                CREATE TABLE IF NOT EXISTS bank_transactions (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    fin_year VARCHAR(10) NOT NULL,
                    bank_account_id INTEGER NOT NULL REFERENCES bank_accounts(id),
                    txn_date DATE NOT NULL,
                    value_date DATE,
                    description TEXT,
                    ref_no VARCHAR(100),
                    debit DECIMAL(14,2) DEFAULT 0.00,
                    credit DECIMAL(14,2) DEFAULT 0.00,
                    balance DECIMAL(14,2),
                    txn_mode VARCHAR(20),
                    ledger_type VARCHAR(20),
                    party_id INTEGER REFERENCES parties(id),
                    narration TEXT,
                    is_reconciled BOOLEAN DEFAULT FALSE,
                    import_batch VARCHAR(50),
                    hash_key VARCHAR(64) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "gstr2b_records": """
                CREATE TABLE IF NOT EXISTS gstr2b_records (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER REFERENCES companies(id),
                    fin_year VARCHAR(10),
                    period VARCHAR(10),
                    supplier_gstin VARCHAR(15),
                    supplier_name VARCHAR(200),
                    invoice_no VARCHAR(100),
                    invoice_date DATE,
                    invoice_type VARCHAR(20) DEFAULT 'B2B',
                    taxable_value DECIMAL(18,2),
                    igst DECIMAL(18,2) DEFAULT 0.00,
                    cgst DECIMAL(18,2) DEFAULT 0.00,
                    sgst DECIMAL(18,2) DEFAULT 0.00,
                    itc_available BOOLEAN DEFAULT TRUE,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "bank_import_logs": """
                CREATE TABLE IF NOT EXISTS bank_import_logs (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    bank_account_id INTEGER REFERENCES bank_accounts(id),
                    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_name VARCHAR(200),
                    total_rows INTEGER DEFAULT 0,
                    imported INTEGER DEFAULT 0,
                    duplicates INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    notes TEXT
                )
            """,
            "audit_trails": """
                CREATE TABLE IF NOT EXISTS audit_trails (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER REFERENCES companies(id),
                    user_id INTEGER REFERENCES users(id),
                    action VARCHAR(50),
                    model_name VARCHAR(100),
                    record_id INTEGER,
                    ip_address VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "stock_ledgers": """
                CREATE TABLE IF NOT EXISTS stock_ledgers (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    fin_year VARCHAR(10),
                    item_id INTEGER NOT NULL REFERENCES items(id),
                    txn_date DATE,
                    txn_type VARCHAR(20),
                    in_qty DECIMAL(18,3) DEFAULT 0.00,
                    out_qty DECIMAL(18,3) DEFAULT 0.00,
                    rate DECIMAL(18,2) DEFAULT 0.00,
                    bill_id INTEGER REFERENCES bills(id)
                )
            """,
            "tds_entries": """
                CREATE TABLE IF NOT EXISTS tds_entries (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    fin_year VARCHAR(10),
                    party_id INTEGER NOT NULL REFERENCES parties(id),
                    section VARCHAR(10),
                    txn_date DATE,
                    amount DECIMAL(18,2) DEFAULT 0.00,
                    tds_rate DECIMAL(5,2) DEFAULT 0.00,
                    tds_amount DECIMAL(18,2) DEFAULT 0.00,
                    is_paid BOOLEAN DEFAULT FALSE,
                    challan_no VARCHAR(50)
                )
            """,
            "compliance_alerts": """
                CREATE TABLE IF NOT EXISTS compliance_alerts (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    alert_type VARCHAR(50),
                    message TEXT,
                    due_date DATE,
                    priority VARCHAR(10) DEFAULT 'Medium',
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "fixed_assets": """
                CREATE TABLE IF NOT EXISTS fixed_assets (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    asset_name VARCHAR(200),
                    asset_category VARCHAR(100),
                    purchase_date DATE,
                    purchase_amount DECIMAL(18,2) DEFAULT 0.00,
                    dep_rate DECIMAL(5,2) DEFAULT 15.00,
                    current_value DECIMAL(18,2) DEFAULT 0.00,
                    is_disposed BOOLEAN DEFAULT FALSE
                )
            """
        }
        
        for table_name, create_sql in tables_to_create.items():
            try:
                cursor.execute(create_sql)
                print(f"[OK] Created {table_name} table")
            except Exception as e:
                print(f"[WARNING]  Error creating {table_name}: {e}")
        
        # 6. Create comprehensive indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_companies_user_id ON user_companies(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_companies_company_id ON user_companies(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_companies_active ON user_companies(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_company_access_log_user_id ON company_access_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_company_access_log_company_id ON company_access_log(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_bills_company_id ON bills(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_bills_fin_year ON bills(fin_year)",
            "CREATE INDEX IF NOT EXISTS idx_bills_bill_type ON bills(bill_type)",
            "CREATE INDEX IF NOT EXISTS idx_bills_bill_date ON bills(bill_date)",
            "CREATE INDEX IF NOT EXISTS idx_parties_company_id ON parties(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_items_company_id ON items(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_company_id ON accounts(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_journal_headers_company_id ON journal_headers(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_journal_lines_header_id ON journal_lines(journal_header_id)",
            "CREATE INDEX IF NOT EXISTS idx_journal_lines_account_id ON journal_lines(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_bill_items_bill_id ON bill_items(bill_id)",
            "CREATE INDEX IF NOT EXISTS idx_bill_items_item_id ON bill_items(item_id)",
            "CREATE INDEX IF NOT EXISTS idx_gst_returns_company_id ON gst_returns(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_tds_returns_company_id ON tds_returns(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_company_id ON alerts(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_loan_applications_company_id ON loan_applications(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_milk_rate_charts_company_id ON milk_rate_charts(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_milk_transactions_company_id ON milk_transactions(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_milk_transactions_party_id ON milk_transactions(party_id)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_invoices_company_id ON purchase_invoices(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_sale_invoices_company_id ON sale_invoices(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_bank_accounts_company_id ON bank_accounts(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_bank_transactions_company_id ON bank_transactions(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_bank_transactions_account_id ON bank_transactions(bank_account_id)",
            "CREATE INDEX IF NOT EXISTS idx_gstr2b_records_company_id ON gstr2b_records(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_bank_import_logs_company_id ON bank_import_logs(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_trails_company_id ON audit_trails(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_ledgers_company_id ON stock_ledgers(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_tds_entries_company_id ON tds_entries(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_compliance_alerts_company_id ON compliance_alerts(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_fixed_assets_company_id ON fixed_assets(company_id)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                print(f"[WARNING]  Index creation issue: {e}")
        
        print("[OK] Created indexes")
        
        # 7. Migrate existing user-company relationships
        try:
            cursor.execute("""
                INSERT INTO user_companies (user_id, company_id, role)
                SELECT id, company_id, role FROM users WHERE company_id IS NOT NULL
                ON CONFLICT DO NOTHING
            """)
            print("[OK] Migrated user-company relationships")
        except Exception as e:
            print(f"[WARNING]  Error migrating relationships: {e}")
        
        # 8. Update first user to super admin
        try:
            cursor.execute("UPDATE users SET is_super_admin = TRUE WHERE id = 1")
            print("[OK] Updated first user to super admin")
        except Exception as e:
            print(f"[WARNING]  Error updating super admin: {e}")
        
        # 9. Update bills table defaults
        try:
            cursor.execute("UPDATE bills SET template_type = 'standard' WHERE template_type IS NULL")
            cursor.execute("UPDATE bills SET is_cancelled = FALSE WHERE is_cancelled IS NULL")
            cursor.execute("UPDATE bills SET tds_rate = 0.00 WHERE tds_rate IS NULL")
            cursor.execute("UPDATE bills SET tds_amount = 0.00 WHERE tds_amount IS NULL")
            cursor.execute("UPDATE bills SET tcs_rate = 0.00 WHERE tcs_rate IS NULL")
            cursor.execute("UPDATE bills SET tcs_amount = 0.00 WHERE tcs_amount IS NULL")
            print("[OK] Updated bills table defaults")
        except Exception as e:
            print(f"[WARNING]  Error updating bills defaults: {e}")
        
        # 10. Fix other common missing columns
        common_table_fixes = {
            "parties": [
                ("gstin", "VARCHAR(15)"),
                ("pan", "VARCHAR(10)"),
                ("state_code", "VARCHAR(2)"),
                ("address", "TEXT"),
                ("phone", "VARCHAR(15)"),
                ("email", "VARCHAR(100)"),
                ("opening_balance", "DECIMAL(18,2) DEFAULT 0.00"),
                ("balance_type", "VARCHAR(2) DEFAULT 'Dr'"),
                ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            ],
            "items": [
                ("hsn_code", "VARCHAR(8)"),
                ("gst_rate", "DECIMAL(5,2) DEFAULT 0.00"),
                ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            ],
            "accounts": [
                ("account_type", "VARCHAR(20)"),
                ("opening_balance", "DECIMAL(12,2) DEFAULT 0.00"),
                ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            ],
            "journal_headers": [
                ("fin_year", "VARCHAR(10)"),
                ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("created_by", "INTEGER")
            ],
            "journal_lines": [
                ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            ],
            "financial_years": [
                ("is_active", "BOOLEAN DEFAULT TRUE"),
                ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            ]
        }
        
        for table_name, columns in common_table_fixes.items():
            for col_name, col_type in columns:
                try:
                    cursor.execute(f"""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = '{table_name}' AND column_name = '{col_name}'
                    """)
                    if not cursor.fetchone():
                        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                        print(f"[OK] Added {col_name} column to {table_name}")
                except Exception as e:
                    print(f"[WARNING]  {table_name}.{col_name} column issue: {e}")
        
        # 11. Update table defaults
        try:
            cursor.execute("UPDATE companies SET business_type = 'service' WHERE business_type IS NULL")
            cursor.execute("UPDATE parties SET gstin = '' WHERE gstin IS NULL")
            cursor.execute("UPDATE parties SET opening_balance = 0.00 WHERE opening_balance IS NULL")
            cursor.execute("UPDATE parties SET balance_type = 'Dr' WHERE balance_type IS NULL")
            cursor.execute("UPDATE items SET gst_rate = 0.00 WHERE gst_rate IS NULL")
            cursor.execute("UPDATE accounts SET opening_balance = 0.00 WHERE opening_balance IS NULL")
            cursor.execute("UPDATE financial_years SET is_active = TRUE WHERE is_active IS NULL")
            print("Updated table defaults")
        except Exception as e:
            print(f"Error updating table defaults: {e}")
        
        conn.commit()
        conn.close()
        print("Comprehensive database migration completed!")
        return True
        
    except Exception as e:
        print(f"Migration error: {e}")
        return False

def create_app():
    # SKIP POSTGRESQL MIGRATION FOR SQLITE DEVELOPMENT
    print("Starting ERP application...")
    # Only run PostgreSQL migration if DATABASE_URL is explicitly set to PostgreSQL
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("postgresql://"):
        migration_success = run_database_migration()
        if not migration_success:
            print("Migration failed, but continuing with app startup...")
    else:
        print("Using SQLite - skipping PostgreSQL migration")
    
    app = Flask(__name__)
    app.config["SECRET_KEY"]                     = os.getenv("SECRET_KEY", "dev-secret")
    # Use SQLite for local development instead of PostgreSQL
    app.config["SQLALCHEMY_DATABASE_URI"]        = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(os.path.dirname(__file__), 'instance', 'erp.db')}")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # TEMPORARY: Disable login requirement for development
    app.config["DISABLE_LOGIN"] = os.getenv("DISABLE_LOGIN", "true").lower() == "true"
    
    # Initialize database
    from extensions import db
    db.init_app(app)
    
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # TEMPORARY: Setup login bypass for Northflank deployment
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request
        if app.config.get('DISABLE_LOGIN', False):
            # Auto-login and redirect instead of showing login page
            from models import User, Company, FinancialYear
            user = User.query.first()
            if user:
                from flask_login import login_user
                login_user(user)
                
                # Set up session for first company
                company = Company.query.first()
                if company:
                    fy = FinancialYear.query.filter_by(company_id=company.id, is_active=True).first()
                    session["company_id"] = company.id
                    session["company_name"] = company.name
                    session["fin_year"] = fy.year_name if fy else "2025-26"
                    session["user_role"] = "admin"
                
                # Redirect back to the requested page (preserve querystring)
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(request.full_path.rstrip('?'))
        return redirect(url_for("auth.login"))

    from modules.auth           import auth_bp
    from modules.journal        import journal_bp
    from modules.clients        import clients_bp
    from modules.invoice        import invoice_bp
    from modules.enhanced_invoice import enhanced_invoice_bp
    from modules.company        import company_bp
    from modules.users          import users_bp
    from modules.items          import items_bp
    from modules.accounts       import accounts_bp
    from modules.parties         import parties_bp
    from modules.gst_module     import gst_bp
    from modules.gst_reports    import gst_reports_bp
    from modules.tds_module     import tds_bp
    from modules.tds_tcs       import tds_tcs_bp
    from modules.alerts_module  import alerts_bp
    from modules.reports_module import reports_bp
    from modules.smf_module     import smf_bp
    from modules.year_module    import year_bp
    from modules.milk           import milk_bp
    from modules.milk_reports   import milk_reports_bp
    from modules.psi            import psi_bp
    from modules.banking        import banking_bp
    from modules.utilities      import utilities_bp
    from modules.fixed_assets   import fixed_assets_bp
    from modules.validators     import validator_bp
    from modules.gst_module     import gst_bp
    from modules.tds_module     import tds_bp
    from modules.cash_book      import cash_book_bp
    from modules.day_book       import day_book_bp
    from modules.universal_invoice import universal_invoice_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(utilities_bp)
    app.register_blueprint(fixed_assets_bp)
    app.register_blueprint(journal_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(invoice_bp)
    app.register_blueprint(enhanced_invoice_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(gst_reports_bp)
    app.register_blueprint(tds_bp)
    app.register_blueprint(tds_tcs_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(smf_bp)
    app.register_blueprint(year_bp)
    app.register_blueprint(milk_bp, url_prefix="/milk")
    app.register_blueprint(milk_reports_bp, url_prefix="/milk")
    app.register_blueprint(parties_bp, url_prefix="/parties")
    app.register_blueprint(banking_bp, url_prefix="/banking")
    app.register_blueprint(validator_bp)
    app.register_blueprint(gst_bp)
    app.register_blueprint(cash_book_bp, url_prefix="/cash-book")
    app.register_blueprint(day_book_bp, url_prefix="/day-book")
    app.register_blueprint(universal_invoice_bp)
    
    # Context processor to make company info available in all templates
    @app.context_processor
    def inject_company_info():
        from models import Company, FinancialYear
        from flask import session
        
        company_name = "No Company"
        company_id = session.get("company_id")
        if company_id:
            company = db.session.get(Company, company_id)
            if company:
                company_name = company.name
        
        # Helper function to get financial years for company
        def get_financial_years_for_company(cid):
            if cid:
                return FinancialYear.query.filter_by(company_id=cid).order_by(FinancialYear.year_name.desc()).all()
            return []
        
        return dict(
            current_company_name=company_name,
            get_financial_years_for_company=get_financial_years_for_company
        )

    with app.app_context():
        try:
            db.create_all()
            print("[OK] Database tables created")
        except Exception as e:
            print(f"[WARNING]  Database setup: {e}")

    @app.route("/")
    def index():
        # TEMPORARY BYPASS FOR NORTHFLANK DEPLOYMENT
        # Remove this block after setting up proper authentication
        if not current_user.is_authenticated:
            # Auto-login as first user for deployment testing
            from models import User, Company, FinancialYear, UserCompany
            user = User.query.first()
            if user:
                from flask_login import login_user
                login_user(user)
                
                # Set up session for first company
                company = Company.query.first()
                if company:
                    fy = FinancialYear.query.filter_by(company_id=company.id, is_active=True).first()
                    session["company_id"] = company.id
                    session["company_name"] = company.name
                    session["fin_year"] = fy.year_name if fy else "2025-26"
                    session["user_role"] = "admin"
        
        if current_user.is_authenticated:
            return redirect(url_for("reports.hub"))
        return redirect(url_for("auth.login"))

    @app.route("/bypass")
    def bypass_login():
        """TEMPORARY: Direct access to reports hub for Northflank testing"""
        # Auto-login as first user
        from models import User, Company, FinancialYear
        user = User.query.first()
        if user:
            from flask_login import login_user
            login_user(user)
            
            # Set up session for first company
            company = Company.query.first()
            if company:
                fy = FinancialYear.query.filter_by(company_id=company.id, is_active=True).first()
                session["company_id"] = company.id
                session["company_name"] = company.name
                session["fin_year"] = fy.year_name if fy else "2025-26"
                session["user_role"] = "admin"
        
        return redirect(url_for("reports.hub"))

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
