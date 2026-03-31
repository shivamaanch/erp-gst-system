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

def emergency_database_fix():
    """Run emergency database fix with proper migration pattern - PostgreSQL only"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found - skipping emergency fix")
        return False
    
    # Only run on PostgreSQL, not SQLite
    if not (db_url.startswith('postgresql://') or db_url.startswith('postgres://')):
        print("🔄 SQLite detected - skipping emergency fix")
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

# Add database connection reset function
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



    return app



app = create_app()



if __name__ == "__main__":

    app.run(debug=True, host="0.0.0.0", port=5000)

