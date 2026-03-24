-- ERP System — PostgreSQL Schema
-- Run: psql -U postgres -d erp_db -f erp_schema.sql

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    gstin VARCHAR(15),
    pan VARCHAR(10),
    state_code VARCHAR(2),
    address TEXT,
    phone VARCHAR(15),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS financial_years (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    year_name VARCHAR(10),
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT FALSE,
    is_closed BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256),
    role VARCHAR(20) DEFAULT 'Staff',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    name VARCHAR(200) NOT NULL,
    group_name VARCHAR(100),
    account_type VARCHAR(50),
    opening_dr NUMERIC(18,2) DEFAULT 0,
    opening_cr NUMERIC(18,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS parties (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    name VARCHAR(200) NOT NULL,
    party_type VARCHAR(20),
    gstin VARCHAR(15),
    pan VARCHAR(10),
    phone VARCHAR(15),
    email VARCHAR(100),
    address TEXT,
    state_code VARCHAR(2),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    name VARCHAR(200) NOT NULL,
    hsn_code VARCHAR(10),
    unit VARCHAR(20),
    gst_rate NUMERIC(5,2) DEFAULT 18,
    purchase_rate NUMERIC(18,2) DEFAULT 0,
    sale_rate NUMERIC(18,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS bills (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    fin_year VARCHAR(10),
    bill_type VARCHAR(20),
    bill_no VARCHAR(50),
    bill_date DATE,
    party_id INTEGER REFERENCES parties(id),
    taxable_amount NUMERIC(18,2) DEFAULT 0,
    cgst NUMERIC(18,2) DEFAULT 0,
    sgst NUMERIC(18,2) DEFAULT 0,
    igst NUMERIC(18,2) DEFAULT 0,
    total_amount NUMERIC(18,2) DEFAULT 0,
    paid_amount NUMERIC(18,2) DEFAULT 0,
    is_cancelled BOOLEAN DEFAULT FALSE,
    narration TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS journal_headers (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    fin_year VARCHAR(10),
    voucher_no VARCHAR(50),
    voucher_type VARCHAR(30),
    voucher_date DATE NOT NULL,
    narration TEXT,
    is_cancelled BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS journal_lines (
    id SERIAL PRIMARY KEY,
    journal_header_id INTEGER REFERENCES journal_headers(id),
    account_id INTEGER REFERENCES accounts(id),
    debit NUMERIC(18,2) DEFAULT 0,
    credit NUMERIC(18,2) DEFAULT 0,
    narration TEXT
);

CREATE TABLE IF NOT EXISTS gstr2b_records (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    fin_year VARCHAR(10),
    period VARCHAR(10),
    supplier_gstin VARCHAR(15),
    supplier_name VARCHAR(200),
    invoice_no VARCHAR(50),
    invoice_date DATE,
    invoice_type VARCHAR(20),
    taxable_value NUMERIC(18,2) DEFAULT 0,
    cgst NUMERIC(18,2) DEFAULT 0,
    sgst NUMERIC(18,2) DEFAULT 0,
    igst NUMERIC(18,2) DEFAULT 0,
    itc_available BOOLEAN DEFAULT TRUE,
    status VARCHAR(30) DEFAULT 'pending',
    recon_status VARCHAR(30),
    diff_amount NUMERIC(18,2) DEFAULT 0,
    itc_accepted BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS compliance_alerts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    alert_type VARCHAR(50),
    message TEXT,
    due_date DATE,
    priority VARCHAR(10) DEFAULT 'Medium',
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tds_entries (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    fin_year VARCHAR(10),
    party_id INTEGER REFERENCES parties(id),
    section VARCHAR(10),
    txn_date DATE,
    amount NUMERIC(18,2) DEFAULT 0,
    tds_rate NUMERIC(5,2) DEFAULT 0,
    tds_amount NUMERIC(18,2) DEFAULT 0,
    is_paid BOOLEAN DEFAULT FALSE,
    challan_no VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS audit_trails (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50),
    model_name VARCHAR(100),
    record_id INTEGER,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
