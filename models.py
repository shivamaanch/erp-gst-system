
from extensions import db
from flask_login import UserMixin
from datetime import datetime, date
from sqlalchemy import Numeric

class Company(db.Model):
    __tablename__ = "companies"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    business_type = db.Column(db.String(20), default="Trading")
    gstin = db.Column(db.String(15))
    pan = db.Column(db.String(10))
    state_code = db.Column(db.String(2))
    address = db.Column(db.Text)
    phone = db.Column(db.String(15))
    email = db.Column(db.String(100))
    logo_path = db.Column(db.String(300))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Multi-company relationships
    users = db.relationship("User", secondary="user_companies", back_populates="accessible_companies", lazy="dynamic", overlaps="user_companies")
    user_companies = db.relationship("UserCompany", back_populates="company", lazy="dynamic", overlaps="users")

class FinancialYear(db.Model):
    __tablename__ = "financial_years"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    year_name = db.Column(db.String(10))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=False)
    is_closed = db.Column(db.Boolean, default=False)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(256))
    is_super_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Legacy field for backward compatibility
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    
    # Relationships for multi-company access
    user_companies = db.relationship("UserCompany", back_populates="user", lazy="dynamic", overlaps="accessible_companies")
    accessible_companies = db.relationship("Company", secondary="user_companies", back_populates="users", lazy="dynamic", overlaps="user_companies")
    
    @property
    def current_company(self):
        """Get current active company from session"""
        from flask import session
        company_id = session.get('company_id')
        if company_id:
            return Company.query.get(company_id)
    
    @property
    def current_role(self):
        """Get user role - simplified for permissions"""
        if self.is_super_admin:
            return "Admin"
        return "User"  # Default role for all users
    
    def has_access_to_company(self, company_id):
        """Check if user has access to a specific company"""
        return UserCompany.query.filter_by(
            user_id=self.id, 
            company_id=company_id, 
            is_active=True
        ).first() is not None
    
    def get_role_in_company(self, company_id):
        """Get user's role in a specific company"""
        user_company = UserCompany.query.filter_by(
            user_id=self.id, 
            company_id=company_id, 
            is_active=True
        ).first()
        return user_company.role if user_company else 'viewer'
    
    def can_manage_all_companies(self):
        """Check if user is super admin"""
        return self.is_super_admin

class UserCompany(db.Model):
    __tablename__ = "user_companies"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    role = db.Column(db.String(20), default="viewer")  # Role per company
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Optional expiry date for temporary access
    
    # Relationships
    user = db.relationship("User", back_populates="user_companies", overlaps="accessible_companies,users")
    company = db.relationship("Company", back_populates="user_companies", overlaps="accessible_companies,users")
    
    def __repr__(self):
        return f"<UserCompany {self.user.username} -> {self.company.name} ({self.role})>"

class CompanyAccessLog(db.Model):
    __tablename__ = "company_access_log"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # 'login', 'logout', 'switch', 'grant', 'revoke'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    # Relationships
    user = db.relationship("User", backref="access_logs")
    company = db.relationship("Company", backref="access_logs")
    
    def __repr__(self):
        return f"<CompanyAccessLog {self.user.username} -> {self.company.name} ({self.action})>"

class Account(db.Model):
    __tablename__ = "accounts"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    name = db.Column(db.String(200), nullable=False)
    group_name = db.Column(db.String(100))
    account_type = db.Column(db.String(50))
    opening_dr = db.Column(Numeric(18,2), default=0)
    opening_cr = db.Column(Numeric(18,2), default=0)
    is_active = db.Column(db.Boolean, default=True)

class JournalHeader(db.Model):
    __tablename__ = "journal_headers"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    fin_year = db.Column(db.String(10))
    voucher_no = db.Column(db.String(50))
    voucher_type = db.Column(db.String(30))
    voucher_date = db.Column(db.Date, nullable=False)
    narration = db.Column(db.Text)
    is_cancelled = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lines = db.relationship("JournalLine", backref="header", lazy=True)

class JournalLine(db.Model):
    __tablename__ = "journal_lines"
    id = db.Column(db.Integer, primary_key=True)
    journal_header_id = db.Column(db.Integer, db.ForeignKey("journal_headers.id"))
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"))
    debit = db.Column(Numeric(18,2), default=0)
    credit = db.Column(Numeric(18,2), default=0)
    narration = db.Column(db.Text)
    account = db.relationship("Account")

class Party(db.Model):
    __tablename__ = "parties"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    name = db.Column(db.String(200), nullable=False)
    party_type = db.Column(db.String(20))
    gstin = db.Column(db.String(15))
    pan = db.Column(db.String(10))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    state_code = db.Column(db.String(2))
    opening_balance = db.Column(Numeric(18,2), default=0)
    balance_type = db.Column(db.String(2), default="Dr")
    is_active = db.Column(db.Boolean, default=True)

class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    name = db.Column(db.String(200), nullable=False)
    hsn_code = db.Column(db.String(10))
    unit = db.Column(db.String(20))
    gst_rate = db.Column(Numeric(5,2), default=18)
    purchase_rate = db.Column(Numeric(18,2), default=0)
    sale_rate = db.Column(Numeric(18,2), default=0)
    is_active = db.Column(db.Boolean, default=True)

class Bill(db.Model):
    __tablename__ = "bills"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    party_id = db.Column(db.Integer, db.ForeignKey("parties.id"))
    bill_type = db.Column(db.String(20))  # Sales, Purchase
    bill_no = db.Column(db.String(50))
    voucher_no = db.Column(db.String(50), index=True)  # Unique voucher number for tracking
    bill_date = db.Column(db.Date, nullable=False)
    fin_year = db.Column(db.String(10))
    narration = db.Column(db.Text)
    taxable_amount = db.Column(Numeric(18,2), default=0)
    cgst = db.Column(Numeric(18,2), default=0)
    sgst = db.Column(Numeric(18,2), default=0)
    igst = db.Column(Numeric(18,2), default=0)
    total_amount = db.Column(Numeric(18,2), default=0)
    paid_amount = db.Column(Numeric(18,2), default=0)
    tds_rate = db.Column(Numeric(5,2), default=0)
    tds_amount = db.Column(Numeric(18,2), default=0)
    tcs_rate = db.Column(Numeric(5,2), default=0)
    tcs_amount = db.Column(Numeric(18,2), default=0)
    template_type = db.Column(db.String(20), default="Trading")
    is_cancelled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    party = db.relationship("Party", backref="bills")
    items = db.relationship("BillItem", backref="bill", lazy=True, cascade="all, delete-orphan")

class BillItem(db.Model):
    __tablename__ = "bill_items"
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey("bills.id"))
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"))
    qty = db.Column(Numeric(18,3), default=0)
    rate = db.Column(Numeric(18,2), default=0)
    taxable_amount = db.Column(Numeric(18,2), default=0)
    gst_rate = db.Column(Numeric(5,2), default=18)
    cgst = db.Column(Numeric(18,2), default=0)
    sgst = db.Column(Numeric(18,2), default=0)
    igst = db.Column(Numeric(18,2), default=0)
    item = db.relationship("Item")


class StockLedger(db.Model):
    __tablename__ = "stock_ledgers"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    fin_year = db.Column(db.String(10))
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"))
    txn_date = db.Column(db.Date)
    txn_type = db.Column(db.String(20))
    in_qty = db.Column(Numeric(18,3), default=0)
    out_qty = db.Column(Numeric(18,3), default=0)
    rate = db.Column(Numeric(18,2), default=0)
    bill_id = db.Column(db.Integer, db.ForeignKey("bills.id"))

class TdsEntry(db.Model):
    __tablename__ = "tds_entries"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    fin_year = db.Column(db.String(10))
    party_id = db.Column(db.Integer, db.ForeignKey("parties.id"))
    section = db.Column(db.String(10))
    txn_date = db.Column(db.Date)
    amount = db.Column(Numeric(18,2), default=0)
    tds_rate = db.Column(Numeric(5,2), default=0)
    tds_amount = db.Column(Numeric(18,2), default=0)
    is_paid = db.Column(db.Boolean, default=False)
    challan_no = db.Column(db.String(50))
    party = db.relationship("Party")

class ComplianceAlert(db.Model):
    __tablename__ = "compliance_alerts"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    alert_type = db.Column(db.String(50))
    message = db.Column(db.Text)
    due_date = db.Column(db.Date)
    priority = db.Column(db.String(10), default="Medium")
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FixedAsset(db.Model):
    __tablename__ = "fixed_assets"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    asset_name = db.Column(db.String(200))
    asset_category = db.Column(db.String(100))
    purchase_date = db.Column(db.Date)
    purchase_amount = db.Column(Numeric(18,2), default=0)
    dep_rate = db.Column(Numeric(5,2), default=15)
    current_value = db.Column(Numeric(18,2), default=0)
    is_disposed = db.Column(db.Boolean, default=False)

class AuditTrail(db.Model):
    __tablename__ = "audit_trails"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(50))
    model_name = db.Column(db.String(100))
    record_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GstReturn(db.Model):
    __tablename__ = "gst_returns"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    return_type = db.Column(db.String(20))
    period = db.Column(db.String(10))
    fin_year = db.Column(db.String(10))
    status = db.Column(db.String(20), default="pending")
    filed_at = db.Column(db.DateTime)
    arn = db.Column(db.String(50))


# ═══════════════════════════════════════════════════════
# Phase 2 Models
# ═══════════════════════════════════════════════════════

class GSTReturn(db.Model):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "gst_returns"
    id           = db.Column(db.Integer, primary_key=True)
    company_id   = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    fin_year     = db.Column(db.String(10), nullable=False)
    return_type  = db.Column(db.String(20), nullable=False)   # GSTR1, GSTR3B
    period       = db.Column(db.String(10))                   # e.g. 03-2026
    status       = db.Column(db.String(20), default="Draft")  # Draft/Filed
    filed_on     = db.Column(db.Date)
    arn          = db.Column(db.String(50))                   # Acknowledgement number
    total_tax    = db.Column(db.Numeric(14,2), default=0)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    company      = db.relationship("Company", backref="gst_returns")


class TDSReturn(db.Model):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "tds_returns"
    id           = db.Column(db.Integer, primary_key=True)
    company_id   = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    fin_year     = db.Column(db.String(10), nullable=False)
    quarter      = db.Column(db.String(5))                    # Q1/Q2/Q3/Q4
    form_type    = db.Column(db.String(10), default="26Q")
    status       = db.Column(db.String(20), default="Pending")
    filed_on     = db.Column(db.Date)
    total_tds    = db.Column(db.Numeric(14,2), default=0)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    company      = db.relationship("Company", backref="tds_returns")


class Alert(db.Model):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "alerts"
    id           = db.Column(db.Integer, primary_key=True)
    company_id   = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    alert_type   = db.Column(db.String(30))                   # gst/tds/invoice/party
    severity     = db.Column(db.String(10), default="info")   # info/warning/danger
    title        = db.Column(db.String(100))
    message      = db.Column(db.Text)
    is_read      = db.Column(db.Boolean, default=False)
    due_date     = db.Column(db.Date)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    company      = db.relationship("Company", backref="alerts")


class LoanApplication(db.Model):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "loan_applications"
    id                  = db.Column(db.Integer, primary_key=True)
    company_id          = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    applicant_name      = db.Column(db.String(100), nullable=False)
    business_name       = db.Column(db.String(150))
    loan_amount         = db.Column(db.Numeric(14,2), nullable=False)
    loan_purpose        = db.Column(db.String(100))
    tenure_months       = db.Column(db.Integer)
    existing_loans      = db.Column(db.Numeric(14,2), default=0)
    collateral_details  = db.Column(db.Text)
    projected_turnover  = db.Column(db.Numeric(14,2), default=0)
    projected_profit    = db.Column(db.Numeric(14,2), default=0)
    status              = db.Column(db.String(20), default="Pending")  # Pending/Approved/Rejected
    created_date        = db.Column(db.Date, default=date.today)
    remarks             = db.Column(db.Text)
    company             = db.relationship("Company", backref="loan_applications")

# ═══ Milk Rate Calculator Models ═══════════════════════════════════════

class MilkRateChart(db.Model):
    __tablename__ = "milk_rate_charts"
    id             = db.Column(db.Integer, primary_key=True)
    company_id     = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    chart_name     = db.Column(db.String(100), nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    fat_rate       = db.Column(db.Numeric(8,4), nullable=False)   # Rate per unit FAT
    snf_rate       = db.Column(db.Numeric(8,4), nullable=False)   # Rate per unit SNF
    base_fat       = db.Column(db.Numeric(5,2), default=0)        # Reference FAT %
    base_snf       = db.Column(db.Numeric(5,2), default=0)        # Reference SNF %
    txn_type       = db.Column(db.String(20), default="Both")     # Purchase/Sale/Both
    is_active      = db.Column(db.Boolean, default=True)
    company        = db.relationship("Company", backref="milk_rate_charts")


class MilkTransaction(db.Model):
    __tablename__ = "milk_transactions"
    id          = db.Column(db.Integer, primary_key=True)
    company_id  = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    fin_year    = db.Column(db.String(10), nullable=False)
    voucher_no  = db.Column(db.String(50), index=True)  # Unique voucher number for tracking
    party_id    = db.Column(db.Integer, db.ForeignKey("parties.id"), nullable=False)
    txn_date    = db.Column(db.Date, nullable=False)
    shift       = db.Column(db.String(10), default="Morning")     # Morning/Evening
    txn_type    = db.Column(db.String(20), nullable=False)        # Purchase/Sale
    qty_liters  = db.Column(db.Numeric(10,2), nullable=False)
    fat         = db.Column(db.Numeric(5,2), nullable=False)      # FAT %
    snf         = db.Column(db.Numeric(5,2), nullable=False)      # SNF %
    clr         = db.Column(db.Numeric(5,2), nullable=True, default=0.0)      # CLR value
    rate        = db.Column(db.Numeric(10,4), nullable=False)     # Calculated rate/liter
    amount      = db.Column(db.Numeric(14,2), nullable=False)
    chart_id    = db.Column(db.Integer, db.ForeignKey("milk_rate_charts.id"))
    narration   = db.Column(db.Text)
    bill_id     = db.Column(db.Integer, db.ForeignKey("bills.id"))
    company     = db.relationship("Company", backref="milk_transactions")
    party       = db.relationship("Party",   backref="milk_transactions")
    chart       = db.relationship("MilkRateChart", backref="transactions")
    bill        = db.relationship("Bill", backref="milk_transactions", foreign_keys=[bill_id])


class CashBook(db.Model):
    __tablename__ = "cash_book"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    fin_year = db.Column(db.String(10), nullable=False)
    voucher_no = db.Column(db.String(50), nullable=False, unique=True)
    transaction_date = db.Column(db.Date, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # Receipt/Payment
    amount = db.Column(db.Numeric(14,2), nullable=False)
    narration = db.Column(db.Text, nullable=False)
    party_name = db.Column(db.String(100))
    payment_mode = db.Column(db.String(20), default="Cash")  # Cash/Bank/Online
    reference_no = db.Column(db.String(50))
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = db.relationship("Company", backref="cash_book_entries")
    account = db.relationship("Account", backref="cash_book_entries")


class DayBook(db.Model):
    __tablename__ = "day_book"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    fin_year = db.Column(db.String(10), nullable=False)
    voucher_no = db.Column(db.String(50), nullable=False, unique=True)
    transaction_date = db.Column(db.Date, nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False)
    debit_amount = db.Column(db.Numeric(14,2), default=0)
    credit_amount = db.Column(db.Numeric(14,2), default=0)
    narration = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = db.relationship("Company", backref="day_book_entries")
    account = db.relationship("Account", backref="day_book_entries")


class PurchaseInvoice(db.Model):
    __tablename__ = "purchase_invoices"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    fin_year = db.Column(db.String(10), nullable=False)
    invoice_no = db.Column(db.String(50), nullable=False, unique=True)
    invoice_date = db.Column(db.Date, nullable=False, default=date.today)
    party_id = db.Column(db.Integer, db.ForeignKey("parties.id"), nullable=False)
    party = db.relationship("Party", backref="purchase_invoices")
    item_name = db.Column(db.String(100))
    qty_liters = db.Column(db.Numeric(10, 2))
    fat_percent = db.Column(db.Numeric(5, 2))
    clr_percent = db.Column(db.Numeric(5, 2))
    rate_per_liter = db.Column(db.Numeric(10, 2))
    snf_percent = db.Column(db.Numeric(5, 2))
    fat_rate = db.Column(db.Numeric(10, 2))
    snf_rate = db.Column(db.Numeric(10, 2))
    fat_kgs = db.Column(db.Numeric(10, 2))
    snf_kgs = db.Column(db.Numeric(10, 2))
    taxable_amount = db.Column(db.Numeric(14, 2))
    gst_rate = db.Column(db.Numeric(5, 2), default=0)
    gst_amount = db.Column(db.Numeric(14, 2))
    total_amount = db.Column(db.Numeric(14, 2))
    narration = db.Column(db.Text)
    is_cancelled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def calculate(self):
        if not all([self.qty_liters, self.fat_percent, self.snf_percent, self.rate_per_liter]): return
        qty = float(self.qty_liters); fat = float(self.fat_percent); snf = float(self.snf_percent); rate = float(self.rate_per_liter)
        self.fat_rate = self.rate_per_liter
        self.snf_rate = self.snf_rate_input if hasattr(self,'snf_rate_input') else self.snf_rate
        self.fat_kgs = round(qty * fat / 100, 4)
        self.snf_kgs = round(qty * snf / 100, 4)
        self.taxable_amount = round((self.fat_kgs * self.fat_rate) + (self.snf_kgs * self.snf_rate), 2)
        self.gst_amount = round(float(self.taxable_amount) * float(self.gst_rate) / 100, 2) if self.gst_rate else 0
        self.total_amount = round(float(self.taxable_amount) + float(self.gst_amount), 2)

class SaleInvoice(db.Model):
    __tablename__ = "sale_invoices"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    fin_year = db.Column(db.String(10), nullable=False)
    invoice_no = db.Column(db.String(50), nullable=False, unique=True)
    invoice_date = db.Column(db.Date, nullable=False, default=date.today)
    party_id = db.Column(db.Integer, db.ForeignKey("parties.id"), nullable=False)
    party = db.relationship("Party", backref="sale_invoices")
    item_name = db.Column(db.String(100))
    qty_liters = db.Column(db.Numeric(10, 2))
    fat_percent = db.Column(db.Numeric(5, 2))
    clr_percent = db.Column(db.Numeric(5, 2))
    rate_per_liter = db.Column(db.Numeric(10, 2))
    snf_percent = db.Column(db.Numeric(5, 2))
    fat_rate = db.Column(db.Numeric(10, 2))
    snf_rate = db.Column(db.Numeric(10, 2))
    fat_kgs = db.Column(db.Numeric(10, 2))
    snf_kgs = db.Column(db.Numeric(10, 2))
    taxable_amount = db.Column(db.Numeric(14, 2))
    gst_rate = db.Column(db.Numeric(5, 2), default=0)
    gst_amount = db.Column(db.Numeric(14, 2))
    total_amount = db.Column(db.Numeric(14, 2))
    narration = db.Column(db.Text)
    is_cancelled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def calculate(self):
        if not all([self.qty_liters, self.fat_percent, self.snf_percent, self.rate_per_liter]): return
        qty = float(self.qty_liters); fat = float(self.fat_percent); snf = float(self.snf_percent); rate = float(self.rate_per_liter)
        self.fat_rate = self.rate_per_liter
        self.snf_rate = self.snf_rate_input if hasattr(self,'snf_rate_input') else self.snf_rate
        self.fat_kgs = round(qty * fat / 100, 4)
        self.snf_kgs = round(qty * snf / 100, 4)
        self.taxable_amount = round((self.fat_kgs * self.fat_rate) + (self.snf_kgs * self.snf_rate), 2)
        self.gst_amount = round(float(self.taxable_amount) * float(self.gst_rate) / 100, 2) if self.gst_rate else 0
        self.total_amount = round(float(self.taxable_amount) + float(self.gst_amount), 2)


# ━━━━ BANKING MODULE MODELS ━━━━
class BankAccount(db.Model):
    __tablename__ = "bank_accounts"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    account_name = db.Column(db.String(150), nullable=False)
    bank_name = db.Column(db.String(100))
    account_no = db.Column(db.String(50))
    ifsc = db.Column(db.String(20))
    branch = db.Column(db.String(100))
    account_type = db.Column(db.String(30), default="Current")   # Current/Savings/OD/CC
    opening_balance = db.Column(db.Numeric(14,2), default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship("BankTransaction", backref="bank_account", lazy="dynamic")
    __table_args__ = (db.UniqueConstraint("company_id","account_no", name="uq_bank_acno"),)

class BankTransaction(db.Model):
    __tablename__ = "bank_transactions"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    fin_year = db.Column(db.String(10), nullable=False)
    bank_account_id = db.Column(db.Integer, db.ForeignKey("bank_accounts.id"), nullable=False)
    txn_date = db.Column(db.Date, nullable=False)
    value_date = db.Column(db.Date)
    description = db.Column(db.Text)
    ref_no = db.Column(db.String(100))          # cheque no / upi ref / neft ref
    debit = db.Column(db.Numeric(14,2), default=0)
    credit = db.Column(db.Numeric(14,2), default=0)
    balance = db.Column(db.Numeric(14,2))
    txn_mode = db.Column(db.String(20))         # CASH/UPI/NEFT/RTGS/IMPS/CHQ/ECS/ATM
    ledger_type = db.Column(db.String(20))      # CASH/PARTY/SUSPENSE/BANK
    party_id = db.Column(db.Integer, db.ForeignKey("parties.id"), nullable=True)
    narration = db.Column(db.Text)
    is_reconciled = db.Column(db.Boolean, default=False)
    import_batch = db.Column(db.String(50))     # batch id for bulk imports
    hash_key = db.Column(db.String(64), unique=True)  # duplicate prevention
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Gstr2bRecord(db.Model):
    __tablename__ = "gstr2b_records"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    fin_year = db.Column(db.String(10))
    period = db.Column(db.String(10))  # MM-YYYY
    supplier_gstin = db.Column(db.String(15))
    supplier_name = db.Column(db.String(200))
    invoice_no = db.Column(db.String(100))
    invoice_date = db.Column(db.Date)
    invoice_type = db.Column(db.String(20), default="B2B")
    taxable_value = db.Column(Numeric(18,2))
    igst = db.Column(Numeric(18,2), default=0)
    cgst = db.Column(Numeric(18,2), default=0)
    sgst = db.Column(Numeric(18,2), default=0)
    itc_available = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default="pending")  # pending, matched, mismatched
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BankImportLog(db.Model):
    __tablename__ = "bank_import_logs"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    bank_account_id = db.Column(db.Integer, db.ForeignKey("bank_accounts.id"))
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_name = db.Column(db.String(200))
    total_rows = db.Column(db.Integer, default=0)
    imported = db.Column(db.Integer, default=0)
    duplicates = db.Column(db.Integer, default=0)
    errors = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
