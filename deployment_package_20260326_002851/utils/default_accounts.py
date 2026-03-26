"""
Default Chart of Accounts
Creates standard account groups and ledgers for new companies
"""

DEFAULT_ACCOUNT_GROUPS = [
    # Assets
    {"name": "Fixed Assets", "group_type": "Asset", "parent": None},
    {"name": "Current Assets", "group_type": "Asset", "parent": None},
    {"name": "Investments", "group_type": "Asset", "parent": None},
    {"name": "Loans & Advances", "group_type": "Asset", "parent": None},
    
    # Liabilities
    {"name": "Capital Account", "group_type": "Liability", "parent": None},
    {"name": "Reserves & Surplus", "group_type": "Liability", "parent": None},
    {"name": "Secured Loans", "group_type": "Liability", "parent": None},
    {"name": "Unsecured Loans", "group_type": "Liability", "parent": None},
    {"name": "Current Liabilities", "group_type": "Liability", "parent": None},
    
    # Income
    {"name": "Direct Income", "group_type": "Income", "parent": None},
    {"name": "Indirect Income", "group_type": "Income", "parent": None},
    
    # Expenses
    {"name": "Direct Expenses", "group_type": "Expense", "parent": None},
    {"name": "Indirect Expenses", "group_type": "Expense", "parent": None},
]

DEFAULT_LEDGERS = [
    # Fixed Assets
    {"name": "Land & Building", "group": "Fixed Assets", "opening_balance": 0},
    {"name": "Plant & Machinery", "group": "Fixed Assets", "opening_balance": 0},
    {"name": "Furniture & Fixtures", "group": "Fixed Assets", "opening_balance": 0},
    {"name": "Vehicles", "group": "Fixed Assets", "opening_balance": 0},
    {"name": "Office Equipment", "group": "Fixed Assets", "opening_balance": 0},
    {"name": "Computers", "group": "Fixed Assets", "opening_balance": 0},
    
    # Current Assets
    {"name": "Sundry Debtors", "group": "Current Assets", "opening_balance": 0},
    {"name": "Stock in Hand", "group": "Current Assets", "opening_balance": 0},
    {"name": "Cash in Hand", "group": "Current Assets", "opening_balance": 0},
    {"name": "Bank Balance", "group": "Current Assets", "opening_balance": 0},
    
    # Investments
    {"name": "Long Term Investments", "group": "Investments", "opening_balance": 0},
    {"name": "Short Term Investments", "group": "Investments", "opening_balance": 0},
    
    # Loans & Advances
    {"name": "Advances to Suppliers", "group": "Loans & Advances", "opening_balance": 0},
    {"name": "Prepaid Expenses", "group": "Loans & Advances", "opening_balance": 0},
    {"name": "Deposits", "group": "Loans & Advances", "opening_balance": 0},
    
    # Capital Account
    {"name": "Share Capital", "group": "Capital Account", "opening_balance": 0},
    {"name": "Proprietor Capital", "group": "Capital Account", "opening_balance": 0},
    
    # Reserves & Surplus
    {"name": "General Reserve", "group": "Reserves & Surplus", "opening_balance": 0},
    {"name": "Profit & Loss A/c", "group": "Reserves & Surplus", "opening_balance": 0},
    
    # Secured Loans
    {"name": "Bank Loans", "group": "Secured Loans", "opening_balance": 0},
    {"name": "Term Loans", "group": "Secured Loans", "opening_balance": 0},
    
    # Unsecured Loans
    {"name": "Directors Loan", "group": "Unsecured Loans", "opening_balance": 0},
    {"name": "Other Loans", "group": "Unsecured Loans", "opening_balance": 0},
    
    # Current Liabilities
    {"name": "Sundry Creditors", "group": "Current Liabilities", "opening_balance": 0},
    {"name": "Outstanding Expenses", "group": "Current Liabilities", "opening_balance": 0},
    {"name": "TDS Payable", "group": "Current Liabilities", "opening_balance": 0},
    {"name": "GST Payable", "group": "Current Liabilities", "opening_balance": 0},
    {"name": "Other Liabilities", "group": "Current Liabilities", "opening_balance": 0},
    
    # Direct Income
    {"name": "Sales", "group": "Direct Income", "opening_balance": 0},
    {"name": "Service Income", "group": "Direct Income", "opening_balance": 0},
    
    # Indirect Income
    {"name": "Interest Received", "group": "Indirect Income", "opening_balance": 0},
    {"name": "Commission Received", "group": "Indirect Income", "opening_balance": 0},
    {"name": "Discount Received", "group": "Indirect Income", "opening_balance": 0},
    {"name": "Other Income", "group": "Indirect Income", "opening_balance": 0},
    
    # Direct Expenses
    {"name": "Opening Stock", "group": "Direct Expenses", "opening_balance": 0},
    {"name": "Purchases", "group": "Direct Expenses", "opening_balance": 0},
    {"name": "Direct Wages", "group": "Direct Expenses", "opening_balance": 0},
    {"name": "Freight Inward", "group": "Direct Expenses", "opening_balance": 0},
    {"name": "Carriage Inward", "group": "Direct Expenses", "opening_balance": 0},
    {"name": "Manufacturing Expenses", "group": "Direct Expenses", "opening_balance": 0},
    
    # Indirect Expenses
    {"name": "Salaries & Wages", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Rent", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Electricity", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Telephone", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Printing & Stationery", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Postage & Courier", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Travelling Expenses", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Conveyance", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Insurance", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Repairs & Maintenance", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Depreciation", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Interest Paid", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Bank Charges", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Professional Fees", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Audit Fees", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Legal Expenses", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Advertisement", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Office Expenses", "group": "Indirect Expenses", "opening_balance": 0},
    {"name": "Miscellaneous Expenses", "group": "Indirect Expenses", "opening_balance": 0},
]


def create_default_accounts(company_id):
    """
    Create default chart of accounts for a new company
    
    Args:
        company_id: ID of the company
    
    Returns:
        Number of accounts created
    """
    from models import Account
    from extensions import db
    
    created_count = 0
    
    # Create ledgers (Account model doesn't have groups, just ledgers with group_name)
    for ledger_data in DEFAULT_LEDGERS:
        existing = Account.query.filter_by(
            company_id=company_id,
            name=ledger_data["name"]
        ).first()
        
        if not existing:
            ledger = Account(
                company_id=company_id,
                name=ledger_data["name"],
                group_name=ledger_data["group"],
                account_type=get_account_type_from_group(ledger_data["group"]),
                is_active=True,
                opening_dr=0,
                opening_cr=0
            )
            db.session.add(ledger)
            created_count += 1
    
    db.session.commit()
    return created_count


def get_account_type_from_group(group_name):
    """Get account type based on group name"""
    for group in DEFAULT_ACCOUNT_GROUPS:
        if group["name"] == group_name:
            return group["group_type"]
    return "Asset"  # Default
