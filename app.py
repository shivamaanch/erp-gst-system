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
        print("🔄 Running comprehensive database migration...")
        
        # 1. Fix users table
        try:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'is_super_admin'
            """)
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE")
                print("✅ Added is_super_admin column to users")
        except Exception as e:
            print(f"⚠️  is_super_admin column issue: {e}")
        
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
                    print(f"✅ Added {col_name} column to companies")
            except Exception as e:
                print(f"⚠️  {col_name} column issue: {e}")
        
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
                    print(f"✅ Added {col_name} column to bills")
            except Exception as e:
                print(f"⚠️  {col_name} column issue: {e}")
        
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
            print("✅ Created user_companies table")
        except Exception as e:
            print(f"⚠️  Error creating user_companies: {e}")
        
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
            print("✅ Created company_access_log table")
        except Exception as e:
            print(f"⚠️  Error creating company_access_log: {e}")
        
        # 5. Create missing tables if they don't exist
        tables_to_create = {
            "gst_returns": """
                CREATE TABLE IF NOT EXISTS gst_returns (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    return_type VARCHAR(10) NOT NULL,
                    return_period VARCHAR(20) NOT NULL,
                    total_turnover DECIMAL(15,2) DEFAULT 0.00,
                    total_tax DECIMAL(15,2) DEFAULT 0.00,
                    igst DECIMAL(15,2) DEFAULT 0.00,
                    cgst DECIMAL(15,2) DEFAULT 0.00,
                    sgst DECIMAL(15,2) DEFAULT 0.00,
                    cess DECIMAL(15,2) DEFAULT 0.00,
                    status VARCHAR(20) DEFAULT 'draft',
                    filed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "tds_entries": """
                CREATE TABLE IF NOT EXISTS tds_entries (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    party_id INTEGER NOT NULL REFERENCES parties(id),
                    bill_no VARCHAR(50),
                    bill_date DATE,
                    tds_section VARCHAR(20),
                    tds_rate DECIMAL(5,2) DEFAULT 0.00,
                    amount DECIMAL(12,2) DEFAULT 0.00,
                    tds_amount DECIMAL(12,2) DEFAULT 0.00,
                    quarter VARCHAR(10),
                    financial_year VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "stock_ledger": """
                CREATE TABLE IF NOT EXISTS stock_ledger (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    item_id INTEGER NOT NULL REFERENCES items(id),
                    transaction_type VARCHAR(20) NOT NULL,
                    quantity DECIMAL(10,2) DEFAULT 0.00,
                    rate DECIMAL(12,2) DEFAULT 0.00,
                    amount DECIMAL(12,2) DEFAULT 0.00,
                    balance_quantity DECIMAL(10,2) DEFAULT 0.00,
                    transaction_date DATE,
                    reference_no VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "fixed_assets": """
                CREATE TABLE IF NOT EXISTS fixed_assets (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    asset_name VARCHAR(200) NOT NULL,
                    asset_type VARCHAR(50),
                    purchase_date DATE,
                    purchase_amount DECIMAL(12,2) DEFAULT 0.00,
                    depreciation_rate DECIMAL(5,2) DEFAULT 0.00,
                    current_value DECIMAL(12,2) DEFAULT 0.00,
                    location VARCHAR(200),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "compliance_alerts": """
                CREATE TABLE IF NOT EXISTS compliance_alerts (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id),
                    alert_type VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    due_date DATE,
                    status VARCHAR(20) DEFAULT 'pending',
                    priority VARCHAR(10) DEFAULT 'medium',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
        }
        
        for table_name, create_sql in tables_to_create.items():
            try:
                cursor.execute(create_sql)
                print(f"✅ Created {table_name} table")
            except Exception as e:
                print(f"⚠️  Error creating {table_name}: {e}")
        
        # 6. Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_companies_user_id ON user_companies(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_companies_company_id ON user_companies(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_companies_active ON user_companies(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_bills_company_id ON bills(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_bills_fin_year ON bills(fin_year)",
            "CREATE INDEX IF NOT EXISTS idx_bills_bill_type ON bills(bill_type)",
            "CREATE INDEX IF NOT EXISTS idx_bills_bill_date ON bills(bill_date)",
            "CREATE INDEX IF NOT EXISTS idx_gst_returns_company_id ON gst_returns(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_tds_entries_company_id ON tds_entries(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_ledger_company_id ON stock_ledger(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_fixed_assets_company_id ON fixed_assets(company_id)",
            "CREATE INDEX IF NOT EXISTS idx_compliance_alerts_company_id ON compliance_alerts(company_id)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                print(f"⚠️  Index creation issue: {e}")
        
        print("✅ Created indexes")
        
        # 7. Migrate existing user-company relationships
        try:
            cursor.execute("""
                INSERT INTO user_companies (user_id, company_id, role)
                SELECT id, company_id, role FROM users WHERE company_id IS NOT NULL
                ON CONFLICT DO NOTHING
            """)
            print("✅ Migrated user-company relationships")
        except Exception as e:
            print(f"⚠️  Error migrating relationships: {e}")
        
        # 8. Update first user to super admin
        try:
            cursor.execute("UPDATE users SET is_super_admin = TRUE WHERE id = 1")
            print("✅ Updated first user to super admin")
        except Exception as e:
            print(f"⚠️  Error updating super admin: {e}")
        
        # 9. Update bills table defaults
        try:
            cursor.execute("UPDATE bills SET template_type = 'standard' WHERE template_type IS NULL")
            cursor.execute("UPDATE bills SET is_cancelled = FALSE WHERE is_cancelled IS NULL")
            cursor.execute("UPDATE bills SET tds_rate = 0.00 WHERE tds_rate IS NULL")
            cursor.execute("UPDATE bills SET tds_amount = 0.00 WHERE tds_amount IS NULL")
            cursor.execute("UPDATE bills SET tcs_rate = 0.00 WHERE tcs_rate IS NULL")
            cursor.execute("UPDATE bills SET tcs_amount = 0.00 WHERE tcs_amount IS NULL")
            print("✅ Updated bills table defaults")
        except Exception as e:
            print(f"⚠️  Error updating bills defaults: {e}")
        
        # 10. Fix other common missing columns
        common_table_fixes = {
            "parties": [
                ("gstin", "VARCHAR(15)"),
                ("pan", "VARCHAR(10)"),
                ("state_code", "VARCHAR(2)"),
                ("address", "TEXT"),
                ("phone", "VARCHAR(15)"),
                ("email", "VARCHAR(100)"),
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
                        print(f"✅ Added {col_name} column to {table_name}")
                except Exception as e:
                    print(f"⚠️  {table_name}.{col_name} column issue: {e}")
        
        # 11. Update table defaults
        try:
            cursor.execute("UPDATE companies SET business_type = 'service' WHERE business_type IS NULL")
            cursor.execute("UPDATE parties SET gstin = '' WHERE gstin IS NULL")
            cursor.execute("UPDATE items SET gst_rate = 0.00 WHERE gst_rate IS NULL")
            cursor.execute("UPDATE accounts SET opening_balance = 0.00 WHERE opening_balance IS NULL")
            cursor.execute("UPDATE financial_years SET is_active = TRUE WHERE is_active IS NULL")
            print("✅ Updated table defaults")
        except Exception as e:
            print(f"⚠️  Error updating table defaults: {e}")
        
        conn.commit()
        conn.close()
        print("🎉 Comprehensive database migration completed!")
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

def create_app():
    # RUN MIGRATION BEFORE APP INITIALIZATION
    print("🚀 Starting ERP application...")
    migration_success = run_database_migration()
    if not migration_success:
        print("⚠️  Migration failed, but continuing with app startup...")
    
    app = Flask(__name__)
    app.config["SECRET_KEY"]                     = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"]        = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # TEMPORARY: Disable login requirement for Northflank deployment
    app.config["DISABLE_LOGIN"] = os.getenv("DISABLE_LOGIN", "false").lower() == "true"

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # TEMPORARY: Setup login bypass for Northflank deployment
    @login_manager.unauthorized_handler
    def unauthorized():
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
                return redirect(url_for("reports.hub"))
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

    app.register_blueprint(auth_bp)
    app.register_blueprint(journal_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(invoice_bp)
    app.register_blueprint(enhanced_invoice_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(gst_bp)
    app.register_blueprint(gst_reports_bp)
    app.register_blueprint(tds_bp)
    app.register_blueprint(tds_tcs_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(smf_bp)
    app.register_blueprint(year_bp)
    app.register_blueprint(milk_bp)
    app.register_blueprint(milk_reports_bp)
    app.register_blueprint(psi_bp)
    app.register_blueprint(banking_bp)

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"db.create_all skipped: {e}")

    @app.context_processor
    def inject_globals():
        return dict(
            company_name=session.get("company_name", ""),
            fin_year=session.get("fin_year", ""),
            alert_count=0,
        )

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
