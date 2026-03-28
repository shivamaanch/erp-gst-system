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
        # Auto-generate voucher number
        voucher_no = next_journal_voucher_no(cid, fy)
        
        voucher_date = datetime.strptime(request.form.get("voucher_date"),"%Y-%m-%d").date()
        voucher_type = request.form.get("voucher_type","Journal")
        narration = request.form.get("narration","")
        
        # Get form arrays
        account_ids = request.form.getlist("account_id[]")
        debits = request.form.getlist("debit[]")
        credits = request.form.getlist("credit[]")
        line_narrations = request.form.getlist("line_narration[]")
        
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
        
        # Create journal lines
        lines_created = 0
        for i in range(len(account_ids)):
            if not account_ids[i]:
                continue
            
            debit = float(debits[i] or 0)
            credit = float(credits[i] or 0)
            
            # Only create line if there's a debit or credit amount
            if debit > 0 or credit > 0:
                db.session.add(JournalLine(
                    journal_header_id=jh.id,
                    account_id=int(account_ids[i]),
                    debit=debit,
                    credit=credit,
                ))
                lines_created += 1
        
        if lines_created >= 2:  # At least 2 lines required for a valid journal
            db.session.commit()
            flash(f"Journal entry {voucher_no} created with {lines_created} lines!", "success")
        else:
            db.session.rollback()
            flash("Journal entry requires at least 2 lines with amounts", "danger")
        
        return redirect(url_for("journal.index"))
    
    return render_template("journal/quick_entry.html", 
                         accounts=accounts,
                         today=datetime.now().date().isoformat())
