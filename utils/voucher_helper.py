"""
Voucher Number Generation Helper
Generates unique voucher numbers for all transaction types
"""

from models import Bill, JournalHeader
from extensions import db
from sqlalchemy import func

def generate_voucher_number(company_id, fin_year, voucher_type):
    """
    Generate unique voucher number
    
    Args:
        company_id: Company ID
        fin_year: Financial year (e.g., "2025-26")
        voucher_type: Type of voucher (Sales, Purchase, Journal, Milk, Payment, Receipt)
    
    Returns:
        Unique voucher number (e.g., "SV/2025-26/0001")
    """
    
    # Voucher type prefixes
    prefixes = {
        'Sales': 'SV',
        'Purchase': 'PV',
        'Journal': 'JV',
        'Milk': 'MV',
        'Payment': 'PY',
        'Receipt': 'RC',
        'Contra': 'CV',
        'Debit Note': 'DN',
        'Credit Note': 'CN'
    }
    
    prefix = prefixes.get(voucher_type, 'VN')  # Default to VN (Voucher Number)
    
    # Get the last voucher number for this type and year
    if voucher_type in ['Sales', 'Purchase']:
        # For Bills
        last_voucher = db.session.query(func.max(Bill.voucher_no)).filter(
            Bill.company_id == company_id,
            Bill.fin_year == fin_year,
            Bill.bill_type == voucher_type,
            Bill.voucher_no.like(f'{prefix}/{fin_year}/%')
        ).scalar()
    elif voucher_type == 'Milk':
        # For Milk Transactions - use raw SQL to avoid model issues
        from sqlalchemy import text
        result = db.session.execute(text("""
            SELECT MAX(voucher_no) as last_voucher 
            FROM milk_transactions 
            WHERE company_id = :company_id AND fin_year = :fin_year 
            AND voucher_no LIKE :prefix_pattern
        """), {
            "company_id": company_id,
            "fin_year": fin_year,
            "prefix_pattern": f'{prefix}/{fin_year}/%'
        })
        last_voucher = result.scalar()
    elif voucher_type == 'Journal':
        # For Journal Entries
        last_voucher = db.session.query(func.max(JournalHeader.voucher_no)).filter(
            JournalHeader.company_id == company_id,
            JournalHeader.fin_year == fin_year,
            JournalHeader.voucher_no.like(f'{prefix}/{fin_year}/%')
        ).scalar()
    else:
        last_voucher = None
    
    # Extract sequence number
    if last_voucher:
        try:
            # Extract number from format: "SV/2025-26/0001"
            parts = last_voucher.split('/')
            if len(parts) == 3:
                seq_num = int(parts[2]) + 1
            else:
                seq_num = 1
        except (ValueError, IndexError):
            seq_num = 1
    else:
        seq_num = 1
    
    # Generate new voucher number
    voucher_no = f"{prefix}/{fin_year}/{seq_num:04d}"
    
    return voucher_no


def validate_voucher_number(voucher_no):
    """
    Validate voucher number format
    
    Args:
        voucher_no: Voucher number to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not voucher_no:
        return False
    
    parts = voucher_no.split('/')
    if len(parts) != 3:
        return False
    
    prefix, year, seq = parts
    
    # Check prefix
    valid_prefixes = ['SV', 'PV', 'JV', 'MV', 'PY', 'RC', 'CV', 'DN', 'CN', 'VN']
    if prefix not in valid_prefixes:
        return False
    
    # Check year format (YYYY-YY)
    if len(year) != 7 or year[4] != '-':
        return False
    
    # Check sequence is numeric
    if not seq.isdigit():
        return False
    
    return True


def get_voucher_type_from_prefix(prefix):
    """
    Get voucher type from prefix
    
    Args:
        prefix: Voucher prefix (e.g., "SV")
    
    Returns:
        Voucher type name
    """
    prefix_map = {
        'SV': 'Sales',
        'PV': 'Purchase',
        'JV': 'Journal',
        'MV': 'Milk',
        'PY': 'Payment',
        'RC': 'Receipt',
        'CV': 'Contra',
        'DN': 'Debit Note',
        'CN': 'Credit Note'
    }
    
    return prefix_map.get(prefix, 'Unknown')
