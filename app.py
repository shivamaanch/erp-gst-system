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

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

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
        if current_user.is_authenticated:
            return redirect(url_for("reports.hub"))
        return redirect(url_for("auth.login"))

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
