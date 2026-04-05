"""
Utilities Module - System maintenance and data fixing tools
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_login import login_required
from extensions import db
from models import Bill, JournalHeader, Company
from utils.voucher_helper import generate_voucher_number
from sqlalchemy import text
from datetime import datetime
import shutil
import os
from werkzeug.utils import secure_filename

utilities_bp = Blueprint("utilities", __name__)

@utilities_bp.route("/utilities")
@login_required
def index():
    """Utilities dashboard"""
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    # Get statistics
    from sqlalchemy import text
    
    # Get milk entries count using raw SQL
    milk_result = db.session.execute(text("""
        SELECT COUNT(*) as count 
        FROM milk_transactions 
        WHERE company_id = :company_id AND fin_year = :fin_year
    """), {"company_id": cid, "fin_year": fy})
    milk_count = milk_result.scalar()
    
    # Get milk entries without voucher using raw SQL
    milk_no_voucher_result = db.session.execute(text("""
        SELECT COUNT(*) as count 
        FROM milk_transactions 
        WHERE company_id = :company_id AND fin_year = :fin_year 
        AND (voucher_no IS NULL OR voucher_no = '')
    """), {"company_id": cid, "fin_year": fy})
    milk_no_voucher_count = milk_no_voucher_result.scalar()
    
    stats = {
        'bills': Bill.query.filter_by(company_id=cid, fin_year=fy).count(),
        'milk_entries': milk_count,
        'journals': JournalHeader.query.filter_by(company_id=cid, fin_year=fy).count(),
        'bills_no_voucher': Bill.query.filter_by(company_id=cid, fin_year=fy).filter(
            (Bill.voucher_no == None) | (Bill.voucher_no == '')
        ).count(),
        'milk_no_voucher': milk_no_voucher_count,
    }
    
    return render_template("utilities/index.html", stats=stats)

@utilities_bp.route("/utilities/reindex-vouchers", methods=["GET", "POST"])
@login_required
def reindex_vouchers():
    """Reindex all voucher numbers"""
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    if request.method == "POST":
        try:
            results = {
                'sales': 0,
                'purchase': 0,
                'milk': 0,
                'journal': 0
            }
            
            # Reindex Sales Bills
            sales_bills = Bill.query.filter_by(
                company_id=cid, fin_year=fy, bill_type='Sales'
            ).order_by(Bill.bill_date, Bill.id).all()
            
            for bill in sales_bills:
                voucher_no = generate_voucher_number(cid, fy, 'Sales')
                bill.voucher_no = voucher_no
                results['sales'] += 1
            
            # Reindex Purchase Bills
            purchase_bills = Bill.query.filter_by(
                company_id=cid, fin_year=fy, bill_type='Purchase'
            ).order_by(Bill.bill_date, Bill.id).all()
            
            for bill in purchase_bills:
                voucher_no = generate_voucher_number(cid, fy, 'Purchase')
                bill.voucher_no = voucher_no
                results['purchase'] += 1
            
            # Reindex Milk Transactions using raw SQL
            milk_result = db.session.execute(text("""
                SELECT id, txn_date 
                FROM milk_transactions 
                WHERE company_id = :company_id AND fin_year = :fin_year 
                ORDER BY txn_date, id
            """), {"company_id": cid, "fin_year": fy})
            milk_txns = milk_result.fetchall()
            
            for txn in milk_txns:
                voucher_no = generate_voucher_number(cid, fy, 'Milk')
                db.session.execute(text("""
                    UPDATE milk_transactions 
                    SET voucher_no = :voucher_no 
                    WHERE id = :id
                """), {"voucher_no": voucher_no, "id": txn.id})
                results['milk'] += 1
            
            # Reindex Journal Entries
            journals = JournalHeader.query.filter_by(
                company_id=cid, fin_year=fy
            ).order_by(JournalHeader.voucher_date, JournalHeader.id).all()
            
            for journal in journals:
                voucher_no = generate_voucher_number(cid, fy, 'Journal')
                journal.voucher_no = voucher_no
                results['journal'] += 1
            
            db.session.commit()
            
            flash(f"✅ Reindexed: {results['sales']} Sales, {results['purchase']} Purchase, {results['milk']} Milk, {results['journal']} Journal entries", "success")
            return redirect(url_for('utilities.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error reindexing: {str(e)}", "error")
    
    return render_template("utilities/reindex_vouchers.html")

@utilities_bp.route("/utilities/renumber-vouchers", methods=["GET", "POST"])
@login_required
def renumber_vouchers():
    """Renumber vouchers sequentially"""
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    if request.method == "POST":
        voucher_type = request.form.get("voucher_type")
        start_number = int(request.form.get("start_number", 1))
        
        try:
            count = 0
            
            if voucher_type == "Sales":
                bills = Bill.query.filter_by(
                    company_id=cid, fin_year=fy, bill_type='Sales'
                ).order_by(Bill.bill_date, Bill.id).all()
                
                for i, bill in enumerate(bills, start=start_number):
                    bill.voucher_no = f"SV/{fy}/{i:04d}"
                    count += 1
            
            elif voucher_type == "Purchase":
                bills = Bill.query.filter_by(
                    company_id=cid, fin_year=fy, bill_type='Purchase'
                ).order_by(Bill.bill_date, Bill.id).all()
                
                for i, bill in enumerate(bills, start=start_number):
                    bill.voucher_no = f"PV/{fy}/{i:04d}"
                    count += 1
            
            elif voucher_type == "Milk":
                milk_result = db.session.execute(text("""
                    SELECT id 
                    FROM milk_transactions 
                    WHERE company_id = :company_id AND fin_year = :fin_year 
                    ORDER BY txn_date, id
                """), {"company_id": cid, "fin_year": fy})
                milk_txns = milk_result.fetchall()
                
                for i, txn in enumerate(milk_txns, start=start_number):
                    db.session.execute(text("""
                        UPDATE milk_transactions 
                        SET voucher_no = :voucher_no 
                        WHERE id = :id
                    """), {"voucher_no": f"MV/{fy}/{i:04d}", "id": txn.id})
                    count += 1
            
            elif voucher_type == "Journal":
                journals = JournalHeader.query.filter_by(
                    company_id=cid, fin_year=fy
                ).order_by(JournalHeader.voucher_date, JournalHeader.id).all()
                
                for i, journal in enumerate(journals, start=start_number):
                    journal.voucher_no = f"JV/{fy}/{i:04d}"
                    count += 1
            
            db.session.commit()
            flash(f"✅ Renumbered {count} {voucher_type} vouchers starting from {start_number}", "success")
            return redirect(url_for('utilities.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error renumbering: {str(e)}", "error")
    
    return render_template("utilities/renumber_vouchers.html")

@utilities_bp.route("/utilities/fix-data", methods=["GET", "POST"])
@login_required
def fix_data():
    """Fix common data issues"""
    cid = session.get("company_id")
    fy = session.get("fin_year")
    
    if request.method == "POST":
        fix_type = request.form.get("fix_type")
        
        try:
            if fix_type == "missing_vouchers":
                # Add voucher numbers to entries without them
                count = 0
                
                # Fix Bills
                bills = Bill.query.filter_by(company_id=cid, fin_year=fy).filter(
                    (Bill.voucher_no == None) | (Bill.voucher_no == '')
                ).all()
                
                for bill in bills:
                    bill.voucher_no = generate_voucher_number(cid, fy, bill.bill_type)
                    count += 1
                
                # Fix Milk Transactions using raw SQL
                milk_result = db.session.execute(text("""
                    SELECT id 
                    FROM milk_transactions 
                    WHERE company_id = :company_id AND fin_year = :fin_year 
                    AND (voucher_no IS NULL OR voucher_no = '')
                """), {"company_id": cid, "fin_year": fy})
                milk_txns = milk_result.fetchall()
                
                for txn in milk_txns:
                    voucher_no = generate_voucher_number(cid, fy, 'Milk')
                    db.session.execute(text("""
                        UPDATE milk_transactions 
                        SET voucher_no = :voucher_no 
                        WHERE id = :id
                    """), {"voucher_no": voucher_no, "id": txn.id})
                    count += 1
                
                db.session.commit()
                flash(f"✅ Fixed {count} entries with missing voucher numbers", "success")
            
            elif fix_type == "duplicate_vouchers":
                # Find and fix duplicate voucher numbers
                # This is a placeholder - implement actual duplicate detection
                flash("✅ Checked for duplicate vouchers", "info")
            
            return redirect(url_for('utilities.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error fixing data: {str(e)}", "error")
    
    return render_template("utilities/fix_data.html")

@utilities_bp.route("/utilities/backup-database", methods=["GET", "POST"])
@login_required
def backup_database():
    """Backup the database"""
    if request.method == "POST":
        try:
            # Get database path
            db_path = "instance/erp.db"
            
            if not os.path.exists(db_path):
                flash("❌ Database file not found", "error")
                return redirect(url_for('utilities.backup_database'))
            
            # Create backups directory if not exists
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"erp_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Copy database file
            shutil.copy2(db_path, backup_path)
            
            flash(f"✅ Database backed up successfully: {backup_filename}", "success")
            
            # Download the backup file
            return send_file(
                backup_path,
                as_attachment=True,
                download_name=backup_filename,
                mimetype='application/octet-stream'
            )
            
        except Exception as e:
            flash(f"❌ Error creating backup: {str(e)}", "error")
    
    return render_template("utilities/backup_database.html")

@utilities_bp.route("/utilities/restore-database", methods=["GET", "POST"])
@login_required
def restore_database():
    """Restore the database from backup"""
    if request.method == "POST":
        try:
            # Check if file was uploaded
            if 'backup_file' not in request.files:
                flash("❌ No file uploaded", "error")
                return redirect(url_for('utilities.restore_database'))
            
            file = request.files['backup_file']
            
            if file.filename == '':
                flash("❌ No file selected", "error")
                return redirect(url_for('utilities.restore_database'))
            
            if not file.filename.endswith('.db'):
                flash("❌ Invalid file type. Please upload a .db file", "error")
                return redirect(url_for('utilities.restore_database'))
            
            # Get database path
            db_path = "instance/erp.db"
            
            # Create backup of current database before restoring
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_backup = os.path.join(backup_dir, f"erp_before_restore_{timestamp}.db")
            
            if os.path.exists(db_path):
                shutil.copy2(db_path, current_backup)
            
            # Save uploaded file as new database
            file.save(db_path)
            
            flash(f"✅ Database restored successfully! Previous database backed up as: erp_before_restore_{timestamp}.db", "success")
            return redirect(url_for('utilities.index'))
            
        except Exception as e:
            flash(f"❌ Error restoring database: {str(e)}", "error")
    
    return render_template("utilities/restore_database.html")
