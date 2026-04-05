# app.py

from flask import Flask, redirect, url_for, session

from flask_login import current_user

from extensions import db, login_manager, migrate

from dotenv import load_dotenv

import os

import warnings

# Suppress SQLAlchemy relationship warnings
warnings.filterwarnings('ignore', r'.*relationship.*will copy column.*conflicts.*')

import psycopg2

import urllib.parse

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT



load_dotenv()

def _ensure_sqlite_milk_transactions_schema(conn):
    from sqlalchemy import text

    exists = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='milk_transactions'")
    ).fetchone()

    create_sql = """
        CREATE TABLE milk_transactions (
            id INTEGER PRIMARY KEY,
            company_id INTEGER NOT NULL,
            fin_year TEXT NOT NULL,
            voucher_no TEXT,
            txn_date DATE NOT NULL,
            shift TEXT DEFAULT 'Morning',
            txn_type TEXT NOT NULL,
            qty_liters NUMERIC(10,2) NOT NULL,
            fat NUMERIC(5,2) NOT NULL,
            snf NUMERIC(5,2) NOT NULL,
            clr NUMERIC(5,2) DEFAULT 0.0,
            rate NUMERIC(10,4) NOT NULL,
            amount NUMERIC(14,2) NOT NULL,
            chart_id INTEGER,
            narration TEXT,
            bill_id INTEGER,
            FOREIGN KEY (company_id) REFERENCES companies(id),
            FOREIGN KEY (chart_id) REFERENCES milk_rate_charts(id),
            FOREIGN KEY (bill_id) REFERENCES bills(id)
        )
    """

    if not exists:
        conn.execute(text(create_sql))
        print("✅ Created milk_transactions table (SQLite)")
        return

    cols = conn.execute(text("PRAGMA table_info(milk_transactions)")).fetchall()
    col_names = [c[1] for c in cols]
    
    # Check if account_id exists and needs to be removed
    if "account_id" in col_names:
        print("🔧 Removing account_id column from milk_transactions (SQLite)")
        # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
        conn.execute(text("ALTER TABLE milk_transactions RENAME TO milk_transactions_old"))
        conn.execute(text(create_sql))
        
        # Copy data excluding account_id
        old_cols = conn.execute(text("PRAGMA table_info(milk_transactions_old)")).fetchall()
        old_col_names = [c[1] for c in old_cols if c[1] != "account_id"]
        
        if old_col_names:
            cols_str = ", ".join(old_col_names)
            conn.execute(text(f"""
                INSERT INTO milk_transactions ({cols_str})
                SELECT {cols_str} FROM milk_transactions_old
            """))
        
        conn.execute(text("DROP TABLE milk_transactions_old"))
        print("✅ Removed account_id column from milk_transactions")
        return
    
    # Handle party_id migration if needed
    if "party_id" in col_names:
        print("🔧 Migrating milk_transactions: removing legacy party_id column (SQLite)")
        conn.execute(text("ALTER TABLE milk_transactions RENAME TO milk_transactions_old"))
        conn.execute(text(create_sql))

        old_cols = conn.execute(text("PRAGMA table_info(milk_transactions_old)")).fetchall()
        old_col_names = {c[1] for c in old_cols}

        new_cols = [
            "id",
            "company_id",
            "fin_year",
            "voucher_no",
            "txn_date",
            "shift",
            "txn_type",
            "qty_liters",
            "fat",
            "snf",
            "clr",
            "rate",
            "amount",
            "chart_id",
            "narration",
            "bill_id",
        ]

    select_expr = []
    for col in new_cols:
        if col in old_col_names:
            if col == "clr":
                select_expr.append("COALESCE(clr, 0) AS clr")
            else:
                select_expr.append(f"{col} AS {col}")
        else:
            if col == "shift":
                select_expr.append("'Morning' AS shift")
            elif col == "clr":
                select_expr.append("0 AS clr")
            else:
                select_expr.append(f"NULL AS {col}")

    insert_sql = (
        f"INSERT INTO milk_transactions ({', '.join(new_cols)}) "
        f"SELECT {', '.join(select_expr)} FROM milk_transactions_old"
    )
    conn.execute(text(insert_sql))
    conn.execute(text("DROP TABLE milk_transactions_old"))
    print("✅ Migration complete: milk_transactions.party_id removed")

def emergency_database_fix():
    """Run emergency database fix with proper migration pattern - PostgreSQL only"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found - skipping emergency fix")
        return False
    
    # Only run on PostgreSQL, not SQLite
    if not (db_url.startswith('postgresql://') or db_url.startswith('postgres://')):
        print("🔄 SQLite detected - running SQLite table creation")
        # For SQLite, we need to create the tables differently
        create_sqlite_tables()
        # Add missing fin_year column if table exists but column doesn't
        add_missing_sqlite_columns()
        return True
    
    try:
        # Import here to avoid circular imports
        from sqlalchemy import text
        
        # Create a minimal Flask app for app context
        temp_app = Flask(__name__)
        temp_app.config["SQLALCHEMY_DATABASE_URI"] = db_url
        temp_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        
        # Initialize database with temp app
        from extensions import db
        db.init_app(temp_app)
        
        with temp_app.app_context():
            engine = db.engine
            
            # Each ALTER runs in its own AUTOCOMMIT connection - nothing can cascade
            all_ddl = [
                "ALTER TABLE milk_transactions ADD COLUMN IF NOT EXISTS bill_id INTEGER",
                "ALTER TABLE milk_transactions ADD COLUMN IF NOT EXISTS fin_year VARCHAR(10)",
                "ALTER TABLE milk_transactions ADD COLUMN IF NOT EXISTS voucher_no VARCHAR(50)",
                "ALTER TABLE milk_transactions ADD COLUMN IF NOT EXISTS clr NUMERIC(6,2)",
                "ALTER TABLE milk_transactions ADD COLUMN IF NOT EXISTS fat NUMERIC(5,2)",
                "ALTER TABLE milk_transactions ADD COLUMN IF NOT EXISTS snf NUMERIC(5,2)",
                "ALTER TABLE milk_transactions ADD COLUMN IF NOT EXISTS rate NUMERIC(10,4)",
                "ALTER TABLE milk_transactions ADD COLUMN IF NOT EXISTS amount NUMERIC(12,2)",
                "ALTER TABLE milk_transactions ADD COLUMN IF NOT EXISTS shift VARCHAR(20)",
                "ALTER TABLE milk_transactions ADD COLUMN IF NOT EXISTS txn_type VARCHAR(20)",
                "ALTER TABLE milk_transactions ADD COLUMN IF NOT EXISTS chart_id VARCHAR(50)",
                "ALTER TABLE milk_transactions ADD COLUMN IF NOT EXISTS narration TEXT",
                # bill_items - complete column list
                "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS qty NUMERIC(12,3)",
                "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS rate NUMERIC(12,4)",
                "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS taxable_amount NUMERIC(12,2)",
                "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS gst_rate NUMERIC(5,2) DEFAULT 0",
                "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS cgst NUMERIC(12,2) DEFAULT 0",
                "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS sgst NUMERIC(12,2) DEFAULT 0",
                "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS igst NUMERIC(12,2) DEFAULT 0",
                "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS item_id INTEGER",
                "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS description TEXT",
                "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS hsn_code VARCHAR(20)",
                "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS unit VARCHAR(20)",
                "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS discount_pct NUMERIC(5,2) DEFAULT 0",
                "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS discount_amt NUMERIC(12,2) DEFAULT 0",
                "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS total_amount NUMERIC(12,2)",
                # bills - complete column list
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS fin_year VARCHAR(10)",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS voucher_no VARCHAR(50)",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS bill_date DATE",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS due_date DATE",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS party_id INTEGER",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS bill_type VARCHAR(20)",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS narration TEXT",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS subtotal NUMERIC(12,2) DEFAULT 0",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS total_gst NUMERIC(12,2) DEFAULT 0",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS total_amount NUMERIC(12,2) DEFAULT 0",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS tds_rate NUMERIC(5,2) DEFAULT 0",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS tds_amount NUMERIC(12,2) DEFAULT 0",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS tcs_rate NUMERIC(5,2) DEFAULT 0",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS tcs_amount NUMERIC(12,2) DEFAULT 0",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS net_amount NUMERIC(12,2) DEFAULT 0",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS is_cancelled BOOLEAN DEFAULT false",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS template_type VARCHAR(50) DEFAULT 'standard'",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'draft'",
                "ALTER TABLE bills ADD COLUMN IF NOT EXISTS created_by INTEGER",
                # journal_headers
                "ALTER TABLE journal_headers ADD COLUMN IF NOT EXISTS fin_year VARCHAR(10)",
                "ALTER TABLE journal_headers ADD COLUMN IF NOT EXISTS created_by INTEGER",
                "ALTER TABLE journal_headers ADD COLUMN IF NOT EXISTS voucher_type VARCHAR(30)",
                "ALTER TABLE journal_headers ADD COLUMN IF NOT EXISTS voucher_no VARCHAR(50)",
                "ALTER TABLE journal_headers ADD COLUMN IF NOT EXISTS narration TEXT",
                "ALTER TABLE journal_headers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
                # journal_lines
                "ALTER TABLE journal_lines ADD COLUMN IF NOT EXISTS debit NUMERIC(15,2) DEFAULT 0",
                "ALTER TABLE journal_lines ADD COLUMN IF NOT EXISTS credit NUMERIC(15,2) DEFAULT 0",
                "ALTER TABLE journal_lines ADD COLUMN IF NOT EXISTS narration TEXT",
                "ALTER TABLE journal_lines ADD COLUMN IF NOT EXISTS party_id INTEGER",
                "ALTER TABLE journal_lines ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
                # parties
                "ALTER TABLE parties ADD COLUMN IF NOT EXISTS gstin VARCHAR(15)",
                "ALTER TABLE parties ADD COLUMN IF NOT EXISTS pan VARCHAR(10)",
                "ALTER TABLE parties ADD COLUMN IF NOT EXISTS state_code VARCHAR(5)",
                "ALTER TABLE parties ADD COLUMN IF NOT EXISTS address TEXT",
                "ALTER TABLE parties ADD COLUMN IF NOT EXISTS phone VARCHAR(20)",
                "ALTER TABLE parties ADD COLUMN IF NOT EXISTS email VARCHAR(100)",
                "ALTER TABLE parties ADD COLUMN IF NOT EXISTS opening_balance NUMERIC(15,2) DEFAULT 0",
                "ALTER TABLE parties ADD COLUMN IF NOT EXISTS balance_type VARCHAR(10) DEFAULT 'Dr'",
                "ALTER TABLE parties ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
                # items
                "ALTER TABLE items ADD COLUMN IF NOT EXISTS hsn_code VARCHAR(20)",
                "ALTER TABLE items ADD COLUMN IF NOT EXISTS gst_rate NUMERIC(5,2) DEFAULT 0",
                "ALTER TABLE items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
                # accounts
                "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS account_type VARCHAR(50)",
                "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS opening_balance NUMERIC(15,2) DEFAULT 0",
                "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
                # financial_years
                "ALTER TABLE financial_years ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT false",
                "ALTER TABLE financial_years ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
                # cash_book
                "ALTER TABLE cash_book ADD COLUMN IF NOT EXISTS company_id INTEGER",
                "ALTER TABLE cash_book ADD COLUMN IF NOT EXISTS fin_year VARCHAR(10)",
                "ALTER TABLE cash_book ADD COLUMN IF NOT EXISTS voucher_no VARCHAR(50)",
                "ALTER TABLE cash_book ADD COLUMN IF NOT EXISTS transaction_date DATE",
                "ALTER TABLE cash_book ADD COLUMN IF NOT EXISTS transaction_type VARCHAR(20)",
                "ALTER TABLE cash_book ADD COLUMN IF NOT EXISTS amount NUMERIC(14,2)",
                "ALTER TABLE cash_book ADD COLUMN IF NOT EXISTS narration TEXT",
                "ALTER TABLE cash_book ADD COLUMN IF NOT EXISTS party_name VARCHAR(100)",
                "ALTER TABLE cash_book ADD COLUMN IF NOT EXISTS payment_mode VARCHAR(20)",
                "ALTER TABLE cash_book ADD COLUMN IF NOT EXISTS reference_no VARCHAR(50)",
                "ALTER TABLE cash_book ADD COLUMN IF NOT EXISTS account_id INTEGER",
                "ALTER TABLE cash_book ADD COLUMN IF NOT EXISTS created_at TIMESTAMP",
                "ALTER TABLE cash_book ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
                # Fix existing balance_type column to allow longer values
                "ALTER TABLE parties ALTER COLUMN balance_type TYPE VARCHAR(10)",
                # Add is_cancelled column to journal_headers
                "ALTER TABLE journal_headers ADD COLUMN IF NOT EXISTS is_cancelled BOOLEAN NOT NULL DEFAULT FALSE",
                # Add account_id column to bank_accounts
                "ALTER TABLE bank_accounts ADD COLUMN IF NOT EXISTS account_id INTEGER",
                # Add expires_at column to user_companies
                "ALTER TABLE user_companies ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP",
            ]

            for sql in all_ddl:
                try:
                    with engine.begin() as conn:
                        conn.execute(text(sql))
                    print(f"✅ {sql[:70]}")
                except Exception as e:
                    print(f"⚠️ {sql[:50]}: {e}")

            # Safe defaults — each in its own connection
            defaults = [
                "UPDATE bills SET template_type = 'standard' WHERE template_type IS NULL",
                "UPDATE parties SET balance_type = 'Dr' WHERE balance_type IS NULL",
                "UPDATE parties SET opening_balance = 0 WHERE opening_balance IS NULL",
            ]
            for sql in defaults:
                try:
                    with engine.begin() as conn:
                        conn.execute(text(sql))
                    print(f"✅ {sql[:70]}")
                except Exception as e:
                    print(f"⚠️ {sql[:50]}: {e}")

            db.session.remove()
            print("🎉 Emergency fix complete!")
            return True
        
    except Exception as e:
        print(f"🚨 Emergency fix failed: {e}")
        return False

def create_sqlite_tables():
    """Create Fixed Assets and Depreciation Blocks tables for SQLite"""
    try:
        # Import here to avoid circular imports
        from sqlalchemy import text, create_engine
        from datetime import datetime
        
        db_url = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(__file__), 'instance', 'erp.db')}")
        engine = create_engine(db_url)
        
        # Create tables using raw SQL for better compatibility
        with engine.begin() as conn:
            _ensure_sqlite_milk_transactions_schema(conn)

            # Create fixed_assets table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS fixed_assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    fin_year VARCHAR(10) NOT NULL,
                    asset_name VARCHAR(200) NOT NULL,
                    asset_category VARCHAR(100) NOT NULL,
                    description TEXT,
                    opening_wdv FLOAT DEFAULT 0.0,
                    purchase_date DATE,
                    purchase_cost FLOAT DEFAULT 0.0,
                    depreciation_method VARCHAR(20) DEFAULT 'WDV',
                    depreciation_rate FLOAT DEFAULT 15.0,
                    depreciation_block VARCHAR(50) DEFAULT 'General',
                    additions FLOAT DEFAULT 0.0,
                    sales FLOAT DEFAULT 0.0,
                    annual_depreciation FLOAT DEFAULT 0.0,
                    closing_wdv FLOAT DEFAULT 0.0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create depreciation_blocks table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS depreciation_blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    block_name VARCHAR(50) NOT NULL,
                    description TEXT,
                    default_rate FLOAT NOT NULL,
                    it_act_rate FLOAT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Verify tables were created
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('fixed_assets', 'depreciation_blocks')"))
            tables = result.fetchall()
            
        print(f"✅ Fixed Assets tables created for SQLite: {[table[0] for table in tables]}")
        return True
        
    except Exception as e:
        print(f"🚨 Failed to create SQLite tables: {e}")
        return False

def add_missing_sqlite_columns():
    """Add missing columns to existing SQLite tables"""
    try:
        # Import here to avoid circular imports
        from sqlalchemy import text, create_engine
        
        db_url = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(__file__), 'instance', 'erp.db')}")
        engine = create_engine(db_url)
        
        with engine.begin() as conn:
            # Check if fixed_assets table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='fixed_assets'"))
            if result.fetchall():
                print("🔍 Checking fixed_assets table schema...")
                columns = conn.execute(text("PRAGMA table_info(fixed_assets)")).fetchall()
                column_names = [col[1] for col in columns]
                print(f"📋 Current columns: {column_names}")
                
                if 'fin_year' not in column_names:
                    print("🔧 Adding missing fin_year column to fixed_assets table")
                    conn.execute(text("ALTER TABLE fixed_assets ADD COLUMN fin_year VARCHAR(10) NOT NULL DEFAULT '2025-26'"))
                    print("✅ Added fin_year column to fixed_assets table")
                else:
                    print("✅ fin_year column already exists")
                
                # Check if other required columns exist
                if 'asset_name' not in column_names:
                    conn.execute(text("ALTER TABLE fixed_assets ADD COLUMN asset_name VARCHAR(200) NOT NULL DEFAULT ''"))
                if 'asset_category' not in column_names:
                    conn.execute(text("ALTER TABLE fixed_assets ADD COLUMN asset_category VARCHAR(100) NOT NULL DEFAULT 'General'"))
                if 'opening_wdv' not in column_names:
                    conn.execute(text("ALTER TABLE fixed_assets ADD COLUMN opening_wdv FLOAT DEFAULT 0.0"))
                if 'depreciation_rate' not in column_names:
                    conn.execute(text("ALTER TABLE fixed_assets ADD COLUMN depreciation_rate FLOAT DEFAULT 15.0"))
                if 'annual_depreciation' not in column_names:
                    conn.execute(text("ALTER TABLE fixed_assets ADD COLUMN annual_depreciation FLOAT DEFAULT 0.0"))
                if 'closing_wdv' not in column_names:
                    conn.execute(text("ALTER TABLE fixed_assets ADD COLUMN closing_wdv FLOAT DEFAULT 0.0"))
                if 'is_active' not in column_names:
                    conn.execute(text("ALTER TABLE fixed_assets ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                
                print("✅ Fixed Assets table updated with missing columns")
            else:
                print("ℹ️ fixed_assets table doesn't exist yet")
            
            # Check depreciation_blocks table
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='depreciation_blocks'"))
            if result.fetchall():
                columns = conn.execute(text("PRAGMA table_info(depreciation_blocks)")).fetchall()
                column_names = [col[1] for col in columns]
                
                if 'block_name' not in column_names:
                    conn.execute(text("ALTER TABLE depreciation_blocks ADD COLUMN block_name VARCHAR(50) NOT NULL DEFAULT 'General'"))
                if 'default_rate' not in column_names:
                    conn.execute(text("ALTER TABLE depreciation_blocks ADD COLUMN default_rate FLOAT NOT NULL DEFAULT 15.0"))
                
                print("✅ Depreciation Blocks table updated with missing columns")
        
        return True
        
    except Exception as e:
        print(f"🚨 Failed to add missing columns: {e}")
        return False

def reset_database_connection():
    """Reset database connection and clear any failed transactions"""
    try:
        from extensions import db
        # Rollback any existing failed transactions
        db.session.rollback()
        # Remove session from pool
        db.session.remove()
        print("🔄 Database connection reset")
    except Exception as e:
        print(f"⚠️ Connection reset failed: {e}")

# Run emergency fix BEFORE importing models or creating app
emergency_database_fix()

def run_database_migration():
    """Run comprehensive database migration - DISABLED - using emergency_database_fix instead"""
    print("🔄 Old migration disabled - using emergency_database_fix instead")
    return True

def create_app():
    print("Starting ERP application...")
    
    # Emergency database fix already runs at startup - no need for old migration

    

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

    

    # CRITICAL: Reset database connection before every request to prevent transaction errors
    @app.before_request
    def reset_db_connection():
        """Reset database connection before each request to prevent transaction errors"""
        try:
            from extensions import db
            # Rollback any existing failed transactions
            db.session.rollback()
            # Remove session from pool to get fresh connection
            db.session.remove()
        except Exception as e:
            print(f"⚠️ DB reset before request failed: {e}")

    

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

        

        return dict(
            current_company_name=company_name,
            get_financial_years_for_company=get_financial_years_for_company
        )
    
    # Add favicon route to eliminate 404 errors
    @app.route('/favicon.ico')
    def favicon():
        return '', 204  # Return no content

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



    @app.route("/debug/db")
    def debug_db():
        """Debug database schema and missing columns"""
        import psycopg2
        import urllib.parse
        
        debug_info = {"database_url": os.getenv("DATABASE_URL", "Not found")}
        
        if os.getenv("DATABASE_URL"):
            try:
                parsed = urllib.parse.urlparse(os.getenv("DATABASE_URL"))
                conn = psycopg2.connect(
                    host=parsed.hostname,
                    port=parsed.port or 5432,
                    database=parsed.path[1:],
                    user=parsed.username,
                    password=parsed.password
                )
                cursor = conn.cursor()
                
                # Check companies table columns
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'companies' 
                    ORDER BY ordinal_position
                """)
                debug_info["companies_columns"] = cursor.fetchall()
                
                # Check cash_book table columns
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'cash_book' 
                    ORDER BY ordinal_position
                """)
                debug_info["cash_book_columns"] = cursor.fetchall()
                
                # Check if is_active exists in companies
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'companies' AND column_name = 'is_active'
                """)
                debug_info["companies_has_is_active"] = bool(cursor.fetchone())
                
                # Check if account_id exists in cash_book
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'cash_book' AND column_name = 'account_id'
                """)
                debug_info["cash_book_has_account_id"] = bool(cursor.fetchone())
                
                conn.close()
                
            except Exception as e:
                debug_info["error"] = str(e)
        
        return debug_info
    
    @app.route("/debug/fix-db")
    def fix_db():
        """Force fix database schema"""
        success = run_database_migration()
        return {"migration_success": success}
    
    @app.route("/debug/companies")
    def debug_companies():
        """Debug company data"""
        from models import Company
        try:
            companies = Company.query.all()
            return {
                "count": len(companies),
                "companies": [{"id": c.id, "name": c.name, "business_type": c.business_type} for c in companies]
            }
        except Exception as e:
            return {"error": str(e)}

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

    # Add session rollback handler to prevent InFailedSqlTransaction errors
    @app.teardown_request
    def handle_teardown(exception=None):
        if exception:
            db.session.rollback()
        db.session.remove()

    return app



app = create_app()



if __name__ == "__main__":

    app.run(debug=True, host="0.0.0.0", port=5000)

