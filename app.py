# app.py
from flask import Flask, redirect, url_for, session
from flask_login import current_user
from extensions import db, login_manager, migrate
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"]                     = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"]        = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # TEMPORARY: Disable login requirement for Northflank deployment
    app.config["DISABLE_LOGIN"] = os.getenv("DISABLE_LOGIN", "false").lower() == "true"

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # AUTOMATIC DATABASE MIGRATION FOR NORTHFLANK
    with app.app_context():
        try:
            # Check if is_super_admin column exists
            from sqlalchemy import text
            result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_super_admin'"))
            if not result.fetchone():
                print("🔄 Running automatic database migration...")
                
                # Add is_super_admin column
                try:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE"))
                    print("✅ Added is_super_admin column")
                except Exception as e:
                    print(f"⚠️  is_super_admin column might already exist: {e}")
                
                # Create user_companies table
                try:
                    db.session.execute(text("""
                        CREATE TABLE IF NOT EXISTS user_companies (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                            role VARCHAR(20) DEFAULT 'viewer',
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Created user_companies table")
                except Exception as e:
                    print(f"⚠️  Error creating user_companies: {e}")
                
                # Create company_access_log table
                try:
                    db.session.execute(text("""
                        CREATE TABLE IF NOT EXISTS company_access_log (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                            action VARCHAR(50) NOT NULL,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            ip_address VARCHAR(45),
                            user_agent TEXT
                        )
                    """))
                    print("✅ Created company_access_log table")
                except Exception as e:
                    print(f"⚠️  Error creating company_access_log: {e}")
                
                # Create indexes
                try:
                    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_companies_user_id ON user_companies(user_id)"))
                    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_companies_company_id ON user_companies(company_id)"))
                    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_companies_active ON user_companies(is_active)"))
                    print("✅ Created indexes")
                except Exception as e:
                    print(f"⚠️  Error creating indexes: {e}")
                
                # Migrate existing user-company relationships
                try:
                    db.session.execute(text("""
                        INSERT INTO user_companies (user_id, company_id, role)
                        SELECT id, company_id, role FROM users WHERE company_id IS NOT NULL
                        ON CONFLICT DO NOTHING
                    """))
                    print("✅ Migrated user-company relationships")
                except Exception as e:
                    print(f"⚠️  Error migrating relationships: {e}")
                
                # Update first user to super admin
                try:
                    db.session.execute(text("UPDATE users SET is_super_admin = TRUE WHERE id = 1"))
                    print("✅ Updated first user to super admin")
                except Exception as e:
                    print(f"⚠️  Error updating super admin: {e}")
                
                db.session.commit()
                print("🎉 Automatic migration completed!")
            else:
                print("✅ Database schema already up to date")
                
        except Exception as e:
            print(f"❌ Migration error: {e}")
            db.session.rollback()
    
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
