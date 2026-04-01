from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_required, current_user
from extensions import db
from models import JournalHeader, JournalLine, Account
from datetime import datetime

journal_bp = Blueprint("journal", __name__)

def next_journal_voucher_no(company_id, fin_year):
    """Generate next journal voucher number"""
    last = JournalHeader.query.filter_by(company_id=company_id, fin_year=fin_year).order_by(JournalHeader.id.desc()).first()
    if last and last.voucher_no:
        try:
            num = int(last.voucher_no.split('-')[-1]) + 1
        except:
            num = 1
    else:
        num = 1
    return f"JNL-{fin_year}-{num:04d}"

@journal_bp.route("/journal")
@login_required
def index():
    cid  = session.get("company_id"); fy = session.get("fin_year")
    page = request.args.get("page",1,type=int); q = request.args.get("q","")
    query = JournalHeader.query.filter_by(company_id=cid,fin_year=fy,is_cancelled=False)
    if q: query = query.filter(JournalHeader.voucher_no.ilike(f"%{q}%"))
    pagination = query.order_by(JournalHeader.voucher_date.desc()).paginate(page=page,per_page=50)
    return render_template("journal/index.html", pagination=pagination, q=q)

@journal_bp.route("/journal/create", methods=["GET","POST"])
@login_required
def create():
    cid = session.get("company_id"); fy = session.get("fin_year")
    accounts = Account.query.filter_by(company_id=cid,is_active=True).order_by(Account.name).all()
    if request.method == "POST":
        # Auto-generate voucher number if not provided
        voucher_no = request.form.get("voucher_no", "").strip()
        if not voucher_no:
            voucher_no = next_journal_voucher_no(cid, fy)
        
        jh = JournalHeader(
            company_id=cid, fin_year=fy,
            voucher_no=voucher_no,
            voucher_type=request.form.get("voucher_type","Journal"),
            voucher_date=datetime.strptime(request.form.get("voucher_date"),"%Y-%m-%d").date(),
            narration=request.form.get("narration",""),
            created_by=current_user.id,
        )
        db.session.add(jh); db.session.flush()
        for i, acc_id in enumerate(request.form.getlist("account_id[]")):
            if not acc_id: continue
            db.session.add(JournalLine(
                journal_header_id=jh.id, account_id=int(acc_id),
                debit=float(request.form.getlist("debit[]")[i] or 0),
                credit=float(request.form.getlist("credit[]")[i] or 0),
            ))
        db.session.commit()
        flash("Journal entry saved.","success")
        return redirect(url_for("journal.index"))
    
    # Generate next voucher number for display
    next_voucher = next_journal_voucher_no(cid, fy)
    return render_template("journal/create.html", accounts=accounts, next_voucher=next_voucher)

@journal_bp.route("/journal/<int:jh_id>")
@login_required
def view(jh_id):
    return render_template("journal/view.html", jh=JournalHeader.query.get_or_404(jh_id))

@journal_bp.route("/journal/<int:jh_id>/cancel")
@login_required
def cancel(jh_id):
    jh = JournalHeader.query.get_or_404(jh_id)
    jh.is_cancelled = True
    db.session.commit()
    flash(f"Journal {jh.voucher_no} cancelled","success")
    return redirect(url_for("journal.index"))

@journal_bp.route("/journal/quick-entry", methods=["GET","POST"])
@login_required
def quick_entry():
    cid = session.get("company_id"); fy = session.get("fin_year")
    accounts = Account.query.filter_by(company_id=cid,is_active=True).order_by(Account.name).all()
    
    if request.method == "POST":
        # Auto-generate voucher number if not provided
        voucher_no = request.form.get("voucher_no", "").strip()
        if not voucher_no:
            voucher_no = next_journal_voucher_no(cid, fy)
        
        voucher_date = datetime.strptime(request.form.get("voucher_date"),"%Y-%m-%d").date()
        voucher_type = request.form.get("voucher_type","Journal")
        narration = request.form.get("narration","")
        
        # Update session with last used date
        session["last_txn_date"] = voucher_date.isoformat()
        
        # Check if this is a single row save or batch save
        single_save = request.form.get("single_save") == "true"
        
        # Create journal header
        jh = JournalHeader(
            company_id=cid, 
            fin_year=fy,
            voucher_no=voucher_no,
            voucher_type=voucher_type,
            voucher_date=voucher_date,
            narration=narration,
            created_by=current_user.id,
        )
        db.session.add(jh)
        db.session.flush()
        
        if single_save:
            # Single row save - get first row data only
            debit_account_id = request.form.get("debit_account_id")
            credit_account_id = request.form.get("credit_account_id")
            debit_amount = float(request.form.get("debit_amount") or 0)
            credit_amount = float(request.form.get("credit_amount") or 0)
            line_narration = request.form.get("line_narration") or f"Journal entry"
            
            lines_created = 0
            if debit_account_id and debit_amount > 0:
                db.session.add(JournalLine(
                    journal_header_id=jh.id,
                    account_id=int(debit_account_id),
                    debit=debit_amount,
                    credit=0,
                ))
                lines_created += 1
            
            if credit_account_id and credit_amount > 0:
                db.session.add(JournalLine(
                    journal_header_id=jh.id,
                    account_id=int(credit_account_id),
                    debit=0,
                    credit=credit_amount,
                ))
                lines_created += 1
            
            if lines_created >= 2:
                db.session.commit()
                flash(f"Journal entry {voucher_no} created successfully!", "success")
            else:
                db.session.rollback()
                flash("Journal entry requires both debit and credit accounts with amounts", "danger")
        else:
            # Batch save (original logic)
            debit_account_ids = request.form.getlist("debit_account_id[]")
            debit_amounts = request.form.getlist("debit_amount[]")
            credit_account_ids = request.form.getlist("credit_account_id[]")
            credit_amounts = request.form.getlist("credit_amount[]")
            line_narrations = request.form.getlist("line_narration[]")
            
            # Create journal lines - each row creates 2 lines (debit and credit)
            lines_created = 0
            for i in range(len(debit_account_ids)):
                if not debit_account_ids[i] or not credit_account_ids[i]:
                    continue
                
                debit_amount = float(debit_amounts[i] or 0)
                credit_amount = float(credit_amounts[i] or 0)
                line_narration = line_narrations[i] or f"Journal entry {i+1}"
                
                # Only create if amounts are provided
                if debit_amount > 0 or credit_amount > 0:
                    # Create debit line
                    if debit_amount > 0:
                        db.session.add(JournalLine(
                            journal_header_id=jh.id,
                            account_id=int(debit_account_ids[i]),
                            debit=debit_amount,
                            credit=0,
                        ))
                        lines_created += 1
                    
                    # Create credit line
                    if credit_amount > 0:
                        db.session.add(JournalLine(
                            journal_header_id=jh.id,
                            account_id=int(credit_account_ids[i]),
                            debit=0,
                            credit=credit_amount,
                        ))
                        lines_created += 1
            
            if lines_created >= 2:  # At least 2 lines required for a valid journal
                db.session.commit()
                flash(f"Journal entry {voucher_no} created with {lines_created} lines!", "success")
            else:
                db.session.rollback()
                flash("Journal entry requires at least 2 lines with amounts", "danger")
        
        return redirect(url_for("journal.index"))
    
    # Default date to last used or today
    default_date = session.get("last_txn_date") or datetime.now().date().isoformat()
    
    return render_template("journal/quick_entry.html", 
                         accounts=accounts,
                         today=default_date)
