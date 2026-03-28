from flask import Blueprint, render_template, request, session
from flask_login import login_required
from extensions import db
from models import Bill, Party, Company, MilkTransaction, BillItem
from datetime import datetime

universal_invoice_bp = Blueprint("universal_invoice", __name__)

@universal_invoice_bp.route("/invoice/<int:bill_id>/view")
@login_required
def view_invoice(bill_id):
    """Universal invoice viewer for all invoice types"""
    cid = session.get("company_id")
    
    # Get bill and related data
    bill = Bill.query.filter_by(id=bill_id, company_id=cid).first_or_404()
    party = Party.query.get(bill.party_id)
    company = Company.query.get(cid)
    
    # Check if this is a milk invoice
    milk_transaction = None
    if bill.bill_type in ['Purchase', 'Sale']:
        milk_transaction = MilkTransaction.query.filter_by(bill_id=bill_id).first()
    
    # Get bill items for regular invoices
    items = []
    if hasattr(bill, 'items') and bill.items:
        items = bill.items
    elif not milk_transaction:
        # Try to get items from BillItem table
        items = BillItem.query.filter_by(bill_id=bill_id).all()
    
    # Determine template type
    template_type = getattr(bill, 'template_type', None)
    if milk_transaction:
        template_type = 'Milk'
    elif not template_type:
        template_type = 'Trading'  # Default template
    
    return render_template("shared/universal_invoice.html",
                         bill=bill,
                         party=party,
                         company=company,
                         items=items,
                         milk_transaction=milk_transaction,
                         template_type=template_type)

@universal_invoice_bp.route("/invoice/<int:bill_id>/print")
@login_required
def print_invoice(bill_id):
    """Print version of universal invoice"""
    cid = session.get("company_id")
    
    # Get bill and related data
    bill = Bill.query.filter_by(id=bill_id, company_id=cid).first_or_404()
    party = Party.query.get(bill.party_id)
    company = Company.query.get(cid)
    
    # Check if this is a milk invoice
    milk_transaction = None
    if bill.bill_type in ['Purchase', 'Sale']:
        milk_transaction = MilkTransaction.query.filter_by(bill_id=bill_id).first()
    
    # Get bill items for regular invoices
    items = []
    if hasattr(bill, 'items') and bill.items:
        items = bill.items
    elif not milk_transaction:
        items = BillItem.query.filter_by(bill_id=bill_id).all()
    
    # Determine template type
    template_type = getattr(bill, 'template_type', None)
    if milk_transaction:
        template_type = 'Milk'
    elif not template_type:
        template_type = 'Trading'  # Default template
    
    return render_template("shared/universal_invoice.html",
                         bill=bill,
                         party=party,
                         company=company,
                         items=items,
                         milk_transaction=milk_transaction,
                         template_type=template_type)

@universal_invoice_bp.route("/invoice/<int:bill_id>/pdf")
@login_required
def pdf_invoice(bill_id):
    """PDF version of universal invoice"""
    cid = session.get("company_id")
    
    # Get bill and related data
    bill = Bill.query.filter_by(id=bill_id, company_id=cid).first_or_404()
    party = Party.query.get(bill.party_id)
    company = Company.query.get(cid)
    
    # Check if this is a milk invoice
    milk_transaction = None
    if bill.bill_type in ['Purchase', 'Sale']:
        milk_transaction = MilkTransaction.query.filter_by(bill_id=bill_id).first()
    
    # Get bill items for regular invoices
    items = []
    if hasattr(bill, 'items') and bill.items:
        items = bill.items
    elif not milk_transaction:
        items = BillItem.query.filter_by(bill_id=bill_id).all()
    
    # Determine template type
    template_type = getattr(bill, 'template_type', None)
    if milk_transaction:
        template_type = 'Milk'
    elif not template_type:
        template_type = 'Trading'  # Default template
    
    # Generate PDF using WeasyPrint or similar
    try:
        from weasyprint import HTML, CSS
        from flask import make_response
        
        # Render template
        html = render_template("shared/universal_invoice.html",
                             bill=bill,
                             party=party,
                             company=company,
                             items=items,
                             milk_transaction=milk_transaction,
                             template_type=template_type)
        
        # Generate PDF
        pdf = HTML(string=html).write_pdf()
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename={bill.bill_no}.pdf'
        
        return response
        
    except ImportError:
        # Fallback to HTML if WeasyPrint is not available
        return render_template("shared/universal_invoice.html",
                             bill=bill,
                             party=party,
                             company=company,
                             items=items,
                             milk_transaction=milk_transaction,
                             template_type=template_type)
