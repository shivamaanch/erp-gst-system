# modules/enhanced_invoice.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, send_file, jsonify
from flask_login import login_required
from extensions import db
from models import Bill, Party, Item, Company, BillItem
from datetime import datetime, date
from sqlalchemy import func
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO
import json

enhanced_invoice_bp = Blueprint("enhanced_invoice", __name__)

# Dynamic table templates for different business types
INVOICE_TEMPLATES = {
    "Trading": {
        "name": "Standard Trading Invoice",
        "columns": ["Item", "Description", "HSN", "Qty", "Unit", "Rate", "Disc%", "Taxable", "GST%", "GST Amount", "Total"],
        "calculations": ["basic", "gst", "total"]
    },
    "Manufacturing": {
        "name": "Manufacturing Invoice",
        "columns": ["Item", "Description", "HSN", "Qty", "Unit", "Rate", "Raw Material Cost", "Manufacturing Cost", "Disc%", "Taxable", "GST%", "GST Amount", "Total"],
        "calculations": ["manufacturing_cost", "gst", "total"]
    },
    "Service": {
        "name": "Service Invoice",
        "columns": ["Service", "Description", "Hours", "Rate", "Disc%", "Taxable", "GST%", "GST Amount", "Total"],
        "calculations": ["service", "gst", "total"]
    },
    "Milk": {
        "name": "Milk Collection Invoice",
        "columns": ["Farmer", "Date", "Fat %", "SNF %", "Quantity (Ltrs)", "Rate/Ltr", "Basic Amount", "Fat Value", "SNF Value", "Total", "Deductions", "Net Amount"],
        "calculations": ["milk_formula", "deductions", "net"]
    }
}

@enhanced_invoice_bp.route("/enhanced-invoice/create", methods=["GET", "POST"])
@login_required
def create_invoice():
    cid = session.get("company_id")
    fy = session.get("fin_year")
    btype = request.args.get("type", "Sales")
    
    if request.method == "POST":
        # Get company to determine business type
        company = Company.query.get(cid)
        template_type = request.form.get("template_type", company.business_type or "Trading")
        
        # Create bill
        bill = Bill(
            company_id=cid,
            party_id=request.form["party_id"],
            bill_type=btype,
            bill_no=request.form["bill_no"],
            bill_date=datetime.strptime(request.form["bill_date"], "%Y-%m-%d").date(),
            fin_year=fy,
            narration=request.form.get("narration", ""),
            is_igst="is_igst" in request.form,
            template_type=template_type,
            created_by=session.get("user_id", 1)
        )
        
        # Calculate totals based on template
        template = INVOICE_TEMPLATES.get(template_type, INVOICE_TEMPLATES["Trading"])
        items_data = json.loads(request.form.get("items_data", "[]"))
        
        total_taxable = 0
        total_cgst = 0
        total_sgst = 0
        total_igst = 0
        
        for item_data in items_data:
            if template_type == "Milk":
                # Milk-specific calculations
                qty = float(item_data.get("qty", 0))
                fat = float(item_data.get("fat", 3.5))
                snf = float(item_data.get("snf", 8.5))
                rate = float(item_data.get("rate", 0))
                
                # SMF formula: (Fat% × 400 + SNF% × 65) × 10 ÷ 100
                fat_value = round((fat / 100) * 400 * 10, 2)
                snf_value = round((snf / 100) * 65 * 10, 2)
                basic_amount = round(qty * rate, 2)
                total_amount = round(fat_value + snf_value, 2)
                taxable_amount = total_amount
                
            else:
                # Standard calculations
                qty = float(item_data.get("qty", 0))
                rate = float(item_data.get("rate", 0))
                discount = float(item_data.get("discount", 0))
                gst_rate = float(item_data.get("gst_rate", 18))
                
                taxable_amount = round(qty * rate * (1 - discount/100), 2)
                gst_amount = round(taxable_amount * gst_rate / 100, 2)
                total_amount = taxable_amount + gst_amount
                
                if bill.is_igst:
                    total_igst += gst_amount
                else:
                    total_cgst += gst_amount / 2
                    total_sgst += gst_amount / 2
            
            total_taxable += taxable_amount
        
        # Update bill totals
        bill.taxable_amount = total_taxable
        bill.cgst = total_cgst
        bill.sgst = total_sgst
        bill.igst = total_igst
        bill.total_amount = total_taxable + total_cgst + total_sgst + total_igst
        
        db.session.add(bill)
        db.session.commit()
        
        flash(f"{btype} invoice created successfully!", "success")
        return redirect(url_for("enhanced_invoice.list_invoices", type=btype))
    
    # Get data for form
    parties = Party.query.filter_by(company_id=cid, is_active=True).all()
    items = Item.query.filter_by(company_id=cid, is_active=True).all()
    company = Company.query.get(cid)
    
    # Generate bill number
    last_bill = Bill.query.filter_by(company_id=cid, bill_type=btype, fin_year=fy).order_by(Bill.id.desc()).first()
    bill_no = f"{btype[0]}{fy[:4]}{(last_bill.id if last_bill else 0) + 1:04d}"
    
    return render_template("enhanced_invoice/create.html",
                         btype=btype, bill_no=bill_no,
                         parties=parties, items=items,
                         company=company,
                         templates=INVOICE_TEMPLATES)

@enhanced_invoice_bp.route("/enhanced-invoice/delete/<int:bill_id>", methods=["POST"])
@login_required
def delete_invoice(bill_id):
    """Delete an invoice"""
    try:
        cid = session.get("company_id")
        bill = Bill.query.filter_by(id=bill_id, company_id=cid).first()
        
        if not bill:
            return jsonify({"success": False, "message": "Invoice not found"})
        
        if bill.is_cancelled:
            return jsonify({"success": False, "message": "Invoice is already cancelled"})
        
        # Delete bill items first
        BillItem.query.filter_by(bill_id=bill_id).delete()
        
        # Delete the bill
        db.session.delete(bill)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Invoice deleted successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})

@enhanced_invoice_bp.route("/enhanced-invoice/list")
@login_required
def list_invoices():
    cid = session.get("company_id")
    fy = session.get("fin_year")
    btype = request.args.get("type", "Sales")
    
    bills = Bill.query.filter_by(
        company_id=cid, fin_year=fy, bill_type=btype, is_cancelled=False
    ).order_by(Bill.bill_date.desc()).all()
    
    return render_template("enhanced_invoice/list.html", bills=bills, btype=btype)

@enhanced_invoice_bp.route("/enhanced-invoice/print/<int:bill_id>")
@login_required
def print_invoice(bill_id):
    cid = session.get("company_id")
    bill = Bill.query.filter_by(id=bill_id, company_id=cid).first_or_404()
    party = Party.query.get(bill.party_id)
    company = Company.query.get(cid)
    
    # Get bill items
    items = BillItem.query.filter_by(bill_id=bill_id).all()
    
    return render_template("enhanced_invoice/print_pdf.html",
                         bill=bill, party=party, company=company,
                         items=items)

@enhanced_invoice_bp.route("/enhanced-invoice/export/<int:bill_id>/<format>")
@login_required
def export_invoice(bill_id, format):
    cid = session.get("company_id")
    bill = Bill.query.filter_by(id=bill_id, company_id=cid).first_or_404()
    party = Party.query.get(bill.party_id)
    company = Company.query.get(cid)
    
    if format == "excel":
        return export_invoice_excel(bill, party, company)
    elif format == "pdf":
        return export_invoice_pdf(bill, party, company)
    else:
        flash("Invalid format", "danger")
        return redirect(url_for("enhanced_invoice.print_invoice", bill_id=bill_id))

def export_invoice_excel(bill, party, company):
    """Export invoice to Excel with beautiful formatting"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Invoice {bill.bill_no}"
    
    # Company header
    ws.merge_cells("A1:H1")
    ws["A1"] = company.name
    ws["A1"].font = Font(bold=True, size=16)
    ws["A1"].alignment = Alignment(horizontal="center")
    
    ws.merge_cells("A2:H2")
    ws["A2"] = company.address or ""
    ws["A2"].alignment = Alignment(horizontal="center")
    
    ws.merge_cells("A3:H3")
    ws["A3"] = f"GSTIN: {company.gstin or 'Not Available'} | PAN: {company.pan or 'Not Available'}"
    ws["A3"].alignment = Alignment(horizontal="center")
    
    # Invoice details
    row = 5
    ws[f"A{row}"] = "Invoice Details:"
    ws[f"A{row}"].font = Font(bold=True)
    row += 1
    
    ws[f"A{row}"] = f"Invoice No: {bill.bill_no}"
    ws[f"C{row}"] = f"Date: {bill.bill_date.strftime('%d-%m-%Y')}"
    row += 1
    
    ws[f"A{row}"] = f"Party: {party.name}"
    ws[f"C{row}"] = f"GSTIN: {party.gstin or 'Not Available'}"
    row += 2
    
    # Items table
    template = INVOICE_TEMPLATES.get(bill.template_type, INVOICE_TEMPLATES["Trading"])
    headers = template["columns"]
    
    ws[f"A{row}"] = "Item Details:"
    ws[f"A{row}"].font = Font(bold=True)
    row += 1
    
    # Header row
    for i, header in enumerate(headers):
        cell = ws.cell(row=row, column=i+1, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
        cell.border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                             top=Side(style='thin'), bottom=Side(style='thin'))
    row += 1
    
    # Data rows (sample data - you'll need to fetch actual items)
    if hasattr(bill, 'items') and bill.items:
        for item in bill.items:
            ws.cell(row=row, column=1, value=item.item.name if item.item else "Item")
            ws.cell(row=row, column=2, value=f"{item.qty or 0}")
            ws.cell(row=row, column=3, value=f"₹{item.rate or 0}")
            ws.cell(row=row, column=4, value=f"₹{item.taxable_amount or 0}")
            ws.cell(row=row, column=5, value=f"₹{(item.taxable_amount or 0) * 0.18}")
            ws.cell(row=row, column=6, value=f"₹{item.taxable_amount * 1.18}")
            row += 1
    
    # Totals
    row += 1
    ws[f"A{row}"] = "Summary:"
    ws[f"A{row}"].font = Font(bold=True)
    row += 1
    
    ws[f"A{row}"] = "Taxable Amount:"
    ws[f"E{row}"] = f"₹{bill.taxable_amount or 0}"
    row += 1
    
    ws[f"A{row}"] = "CGST:"
    ws[f"E{row}"] = f"₹{bill.cgst or 0}"
    row += 1
    
    ws[f"A{row}"] = "SGST:"
    ws[f"E{row}"] = f"₹{bill.sgst or 0}"
    row += 1
    
    ws[f"A{row}"] = "IGST:"
    ws[f"E{row}"] = f"₹{bill.igst or 0}"
    row += 1
    
    ws[f"A{row}"] = "Total Amount:"
    ws[f"E{row}"] = f"₹{bill.total_amount or 0}"
    ws[f"A{row}"].font = Font(bold=True)
    ws[f"E{row}"].font = Font(bold=True)
    
    # Bank details
    row += 2
    ws[f"A{row}"] = "Bank Details:"
    ws[f"A{row}"].font = Font(bold=True)
    row += 1
    
    ws[f"A{row}"] = "Account Name: " + (company.name or "")
    ws[f"A{row+1}"] = "Account Number: " + ("[Your Bank Account]" or "")
    ws[f"A{row+2}"] = "IFSC Code: " + ("[Your IFSC]" or "")
    ws[f"A{row+3}"] = "Bank Name: " + ("[Your Bank Name]" or "")
    
    # Auto-size columns
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(output, download_name=f"Invoice_{bill.bill_no}.xlsx", as_attachment=True,
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def export_invoice_pdf(bill, party, company):
    """Export invoice to PDF (placeholder - you'll need to add PDF library like WeasyPrint)"""
    # For now, return the HTML template which can be printed to PDF
    return render_template("enhanced_invoice/print_pdf.html",
                         bill=bill, party=party, company=company)

@enhanced_invoice_bp.route("/api/template-fields/<template_type>")
@login_required
def get_template_fields(template_type):
    """API to get fields for dynamic template"""
    template = INVOICE_TEMPLATES.get(template_type, INVOICE_TEMPLATES["Trading"])
    return jsonify(template)
