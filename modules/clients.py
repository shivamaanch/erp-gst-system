# modules/clients.py
from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Party, Bill, Account
clients_bp = Blueprint("clients", __name__)

PARTY_TYPES = ["Debtor", "Creditor", "Supplier", "Both"]


def _fy_aliases(fy: str):
    if not fy:
        return []
    aliases = {fy}
    # Accept both 2025-26 and 25-26 style FY strings
    if len(fy) == 7 and fy[4] == "-":
        aliases.add(f"{fy[2:4]}-{fy[5:7]}")
    elif len(fy) == 5 and fy[2] == "-":
        aliases.add(f"20{fy}")
    return list(aliases)

@clients_bp.route("/clients")
@login_required
def index():
    cid  = session.get("company_id")
    ptype = request.args.get("type", "")
    search = request.args.get("q", "")
    group = request.args.get("group", "")
    fy = request.args.get("fy", "")
    
    # Get all parties
    q = Party.query.filter_by(company_id=cid, is_active=True)
    if ptype:
        q = q.filter_by(party_type=ptype)
    if search:
        q = q.filter(Party.name.ilike(f"%{search}%"))
    parties = q.order_by(Party.name).all()
    
    # Get all accounts (including default system accounts)
    from models import Account
    account_query = Account.query.filter_by(company_id=cid, is_active=True)
    if search:
        account_query = account_query.filter(Account.name.ilike(f"%{search}%"))
    
    # Filter by account type if specified
    if ptype:
        if ptype == "Debtor":
            account_query = account_query.filter(Account.group_name.like("%Debtor%"))
        elif ptype == "Creditor":
            account_query = account_query.filter(Account.group_name.like("%Creditor%"))
        elif ptype == "Cash":
            account_query = account_query.filter(Account.account_type == "Cash")
    
    # Filter by group if specified
    if group:
        account_query = account_query.filter(Account.group_name == group)
    
    accounts = account_query.order_by(Account.name).all()
    
    # Combine parties and accounts for display
    all_entities = []
    
    # Add parties
    for party in parties:
        all_entities.append({
            'id': party.id,
            'name': party.name,
            'type': 'Party',
            'party_type': party.party_type or 'Both',
            'gstin': party.gstin,
            'phone': party.phone,
            'email': party.email,
            'address': party.address,
            'opening_balance': party.opening_balance or 0,
            'balance_type': party.balance_type or 'Dr',
            'is_party': True
        })
    
    # Add accounts
    for account in accounts:
        # Show all accounts (no party_id filtering since it doesn't exist)
        all_entities.append({
            'id': account.id,
            'name': account.name,
            'type': 'Account',
            'party_type': get_account_party_type(account.group_name),
            'gstin': None,
            'phone': None,
            'email': None,
            'address': None,
            'opening_balance': float(account.opening_dr or 0) - float(account.opening_cr or 0),
            'balance_type': 'Dr' if (float(account.opening_dr or 0) - float(account.opening_cr or 0)) >= 0 else 'Cr',
            'is_party': False,
            'account_type': account.account_type,
            'group_name': account.group_name
        })
    
    # Sort by name
    all_entities.sort(key=lambda x: x['name'])
    
    return render_template("clients/index.html", entities=all_entities, ptype=ptype, search=search, party_types=PARTY_TYPES)

def get_account_party_type(group_name):
    """Determine party type based on account group name"""
    if not group_name:
        return 'Both'
    
    group_lower = group_name.lower()
    if 'debtor' in group_lower or 'sundry debtor' in group_lower or 'customer' in group_lower:
        return 'Debtor'
    elif 'creditor' in group_lower or 'sundry creditor' in group_lower or 'supplier' in group_lower:
        return 'Creditor'
    elif 'cash' in group_lower:
        return 'Cash'
    else:
        return 'Both'

@clients_bp.route("/clients/add", methods=["GET","POST"])
@login_required
def add():
    cid = session.get("company_id")
    if request.method == "POST":
        p = Party(
            company_id   = cid,
            name         = request.form["name"].strip(),
            gstin        = request.form.get("gstin","").strip().upper() or None,
            party_type   = request.form["party_type"],
            phone        = request.form.get("phone","").strip() or None,
            email        = request.form.get("email","").strip() or None,
            address      = request.form.get("address","").strip() or None,
            pan          = request.form.get("pan","").strip().upper() or None,
            opening_balance = float(request.form.get("opening_balance") or 0),
            balance_type = request.form.get("balance_type","Dr"),
            is_active    = True
        )
        db.session.add(p)
        db.session.commit()
        flash(f"Party '{p.name}' added successfully!", "success")
        return redirect(url_for("clients.index"))
    return render_template("clients/form.html", party=None, party_types=PARTY_TYPES, title="Add Party")

@clients_bp.route("/clients/edit/<int:pid>", methods=["GET","POST"])
@login_required
def edit(pid):
    cid = session.get("company_id")
    p   = Party.query.filter_by(id=pid, company_id=cid).first_or_404()
    if request.method == "POST":
        p.name         = request.form["name"].strip()
        p.gstin        = request.form.get("gstin","").strip().upper() or None
        p.party_type   = request.form["party_type"]
        p.phone        = request.form.get("phone","").strip() or None
        p.email        = request.form.get("email","").strip() or None
        p.address      = request.form.get("address","").strip() or None
        p.pan          = request.form.get("pan","").strip().upper() or None
        p.opening_balance = float(request.form.get("opening_balance") or 0)
        p.balance_type = request.form.get("balance_type","Dr")
        db.session.commit()
        flash(f"Party '{p.name}' updated!", "success")
        return redirect(url_for("clients.index"))
    return render_template("clients/form.html", party=p, party_types=PARTY_TYPES, title="Edit Party")

@clients_bp.route("/clients/delete/<int:pid>", methods=["POST"])
@login_required
def delete(pid):
    cid = session.get("company_id")
    p   = Party.query.filter_by(id=pid, company_id=cid).first_or_404()
    
    try:
        # Delete all bills associated with this party
        from models import Bill, BillItem, JournalHeader, JournalLine, MilkTransaction
        
        # Get all bills for this party
        bills = Bill.query.filter_by(party_id=pid, company_id=cid).all()
        
        for bill in bills:
            print(f"DEBUG: Deleting bill {bill.id} - {bill.bill_no}")
            
            # Delete bill items
            BillItem.query.filter_by(bill_id=bill.id).delete()
            
            # Find and delete journal entries linked to this bill
            journal_headers = JournalHeader.query.filter(
                JournalHeader.narration.like(f"%{bill.bill_no}%")
            ).all()
            
            for header in journal_headers:
                print(f"DEBUG: Deleting journal header {header.id} and its lines")
                # Delete all journal lines for this header
                JournalLine.query.filter_by(journal_header_id=header.id).delete()
                # Delete the header
                db.session.delete(header)
            
            # Delete the bill
            db.session.delete(bill)
        
        # Delete any milk transactions linked to this party's account
        # Find the account linked to this party
        from models import Account
        account = Account.query.filter_by(company_id=cid, name=p.name).first()
        if account:
            # Delete milk transactions for this account
            milk_txns = MilkTransaction.query.filter_by(account_id=account.id).all()
            for txn in milk_txns:
                print(f"DEBUG: Deleting milk transaction {txn.id}")
                db.session.delete(txn)
        
        # Delete any journal entries directly linked to this party's account
        if account:
            # Find all journal lines for this account
            journal_lines = JournalLine.query.filter_by(account_id=account.id).all()
            for line in journal_lines:
                # Get the header and delete all lines for this header
                header = JournalHeader.query.get(line.journal_header_id)
                if header:
                    print(f"DEBUG: Deleting journal header {header.id} (account cleanup)")
                    JournalLine.query.filter_by(journal_header_id=header.id).delete()
                    db.session.delete(header)
        
        # Finally delete the party
        db.session.delete(p)
        db.session.commit()
        
        flash(f"Party '{p.name}' and all associated transactions deleted permanently.", "success")
        return redirect(url_for("clients.index"))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting party: {str(e)}", "danger")
        return redirect(url_for("clients.index"))

@clients_bp.route("/clients/delete-account/<int:aid>", methods=["POST"])
@login_required
def delete_account(aid):
    cid = session.get("company_id")
    from models import Account
    account = Account.query.filter_by(id=aid, company_id=cid).first_or_404()
    
    try:
        # Delete all associated transactions for this account
        from models import Bill, BillItem, JournalHeader, JournalLine, MilkTransaction
        
        # Find bills linked to this account (by matching account name with party name)
        # First find parties with this name
        from models import Party
        parties = Party.query.filter_by(name=account.name, company_id=cid).all()
        party_ids = [p.id for p in parties]
        
        # Delete bills for these parties
        if party_ids:
            bills = Bill.query.filter(Bill.party_id.in_(party_ids), Bill.company_id == cid).all()
            for bill in bills:
                print(f"DEBUG: Deleting bill {bill.id} - {bill.bill_no}")
                # Delete bill items
                BillItem.query.filter_by(bill_id=bill.id).delete()
                # Delete journal entries linked to this bill
                journal_headers = JournalHeader.query.filter(
                    JournalHeader.narration.like(f"%{bill.bill_no}%")
                ).all()
                for header in journal_headers:
                    print(f"DEBUG: Deleting journal header {header.id} and its lines")
                    JournalLine.query.filter_by(journal_header_id=header.id).delete()
                    db.session.delete(header)
                # Delete the bill
                db.session.delete(bill)
            
            # Delete the party records themselves
            for party in parties:
                print(f"DEBUG: Deleting party {party.id} - {party.name}")
                db.session.delete(party)
        
        # Delete milk transactions for this account
        milk_txns = MilkTransaction.query.filter_by(account_id=account.id).all()
        for txn in milk_txns:
            print(f"DEBUG: Deleting milk transaction {txn.id}")
            db.session.delete(txn)
        
        # Delete all journal entries for this account
        journal_lines = JournalLine.query.filter_by(account_id=account.id).all()
        for line in journal_lines:
            # Get the header and delete all lines for this header
            header = JournalHeader.query.get(line.journal_header_id)
            if header:
                print(f"DEBUG: Deleting journal header {header.id} (account cleanup)")
                JournalLine.query.filter_by(journal_header_id=header.id).delete()
                db.session.delete(header)
        
        # Finally delete the account
        db.session.delete(account)
        db.session.commit()
        
        flash(f"Account '{account.name}' and all associated transactions deleted permanently.", "success")
        return redirect(url_for("clients.index"))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting account: {str(e)}", "danger")
        return redirect(url_for("clients.index"))

@clients_bp.route("/clients/view/<int:pid>")
@login_required
def view(pid):
    cid = session.get("company_id")
    fy  = session.get("fin_year")
    p   = Party.query.filter_by(id=pid, company_id=cid).first_or_404()
    from models import Bill
    fy_list = _fy_aliases(fy)
    q = Bill.query.filter(
        Bill.company_id == cid,
        Bill.party_id == pid,
        Bill.is_cancelled == False,
    )
    if fy_list:
        q = q.filter(Bill.fin_year.in_(fy_list))
    bills = q.order_by(Bill.bill_date.desc()).all()
    return render_template("clients/view.html", party=p, bills=bills)

@clients_bp.route("/api/party-search")
@login_required
def party_search():
    cid = session.get("company_id")
    q   = request.args.get("q","")
    ptype = request.args.get("type","")
    query = Party.query.filter_by(company_id=cid, is_active=True)
    if ptype:
        query = query.filter(Party.party_type.in_([ptype, "Both"]))
    if q:
        query = query.filter(Party.name.ilike(f"%{q}%"))
    results = [{"id": p.id, "name": p.name, "gstin": p.gstin or "", "type": p.party_type} for p in query.limit(20).all()]
    return jsonify(results)

@clients_bp.route("/clients/quick-add", methods=["POST"])
@login_required
def quick_add():
    try:
        cid = session.get("company_id")
        name = request.form.get("name","").strip()
        if not name:
            return jsonify({"success": False, "error": "Party name required"}), 400
        requested_party_type = (request.form.get("party_type", "") or "").strip()
        normalized_party_type = {
            "customer": "Debtor",
            "debtor": "Debtor",
            "sales": "Debtor",
            "supplier": "Supplier",
            "vendor": "Supplier",
            "creditor": "Creditor",
            "purchase": "Supplier",
            "both": "Both"
        }.get(requested_party_type.lower(), "Debtor")
        
        p = Party(
            company_id=cid,
            name=name,
            gstin=request.form.get("gstin","").strip().upper() or None,
            phone=request.form.get("phone","").strip() or None,
            party_type=normalized_party_type,
            is_active=True
        )
        db.session.add(p)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "party": {
                "id": p.id,
                "name": p.name,
                "gstin": p.gstin or "",
                "phone": p.phone or "",
                "party_type": p.party_type
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@clients_bp.route("/api/accounts/<int:account_id>", methods=["PUT"])
@login_required
def update_account(account_id):
    """Update account details via API"""
    try:
        cid = session.get("company_id")
        account = Account.query.filter_by(id=account_id, company_id=cid).first()
        
        if not account:
            return jsonify({"success": False, "message": "Account not found"}), 404
            
        data = request.get_json()
        if 'name' in data:
            account.name = data['name'].strip()
        if 'group_name' in data:
            account.group_name = data['group_name'].strip()
            
        db.session.commit()
        return jsonify({"success": True, "message": "Account updated successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@clients_bp.route("/api/account/<int:account_id>/balance", methods=["PUT"])
@login_required
def update_account_balance(account_id):
    """Update account opening balance via API"""
    try:
        cid = session.get("company_id")
        account = Account.query.filter_by(id=account_id, company_id=cid).first()
        
        if not account:
            return jsonify({"success": False, "message": "Account not found"}), 404
            
        data = request.get_json()
        field = data.get('field')
        value = data.get('value', 0)
        
        if field == 'opening_dr':
            account.opening_dr = value
        elif field == 'opening_cr':
            account.opening_cr = value
        else:
            return jsonify({"success": False, "message": "Invalid field"}), 400
            
        db.session.commit()
        return jsonify({"success": True, "message": "Balance updated successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@clients_bp.route("/api/party/<int:party_id>/balance", methods=["PUT"])
@login_required
def update_party_balance(party_id):
    """Update party opening balance via API"""
    try:
        cid = session.get("company_id")
        party = Party.query.filter_by(id=party_id, company_id=cid).first()
        
        if not party:
            return jsonify({"success": False, "message": "Party not found"}), 404
            
        data = request.get_json()
        field = data.get('field')
        value = data.get('value', 0)
        
        # Update party opening balance based on field
        if field == 'opening_dr':
            party.opening_balance = abs(value)
            party.balance_type = 'Dr'
        elif field == 'opening_cr':
            party.opening_balance = abs(value)
            party.balance_type = 'Cr'
        else:
            return jsonify({"success": False, "message": "Invalid field"}), 400
            
        db.session.commit()
        return jsonify({"success": True, "message": "Balance updated successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@clients_bp.route("/api/balance-sheet")
@login_required
def get_balance_sheet():
    """Get balance sheet data for opening balances"""
    try:
        cid = session.get("company_id")
        year = request.args.get("year", "2025-26")
        date = request.args.get("date", "2025-04-01")
        
        # Get all accounts for the company
        accounts = Account.query.filter_by(company_id=cid, is_active=True).order_by(Account.group_name, Account.name).all()
        
        # Categorize accounts
        assets = []
        liabilities = []
        
        for account in accounts:
            account_data = {
                'id': account.id,
                'name': account.name,
                'group_name': account.group_name,
                'account_type': account.account_type,
                'opening_dr': float(account.opening_dr or 0),
                'opening_cr': float(account.opening_cr or 0)
            }
            
            # Determine if asset or liability based on group name
            group_lower = (account.group_name or "").lower()
            if any(keyword in group_lower for keyword in ['asset', 'cash', 'bank', 'debtor', 'stock', 'investment']):
                assets.append(account_data)
            elif any(keyword in group_lower for keyword in ['liability', 'creditor', 'capital', 'loan', 'provision']):
                liabilities.append(account_data)
            elif account.account_type and 'asset' in account.account_type.lower():
                assets.append(account_data)
            else:
                # Default to liability if unsure
                liabilities.append(account_data)
        
        # Calculate totals
        total_assets = sum(acc['opening_dr'] for acc in assets) - sum(acc['opening_cr'] for acc in assets)
        total_liabilities = sum(acc['opening_cr'] for acc in liabilities) - sum(acc['opening_dr'] for acc in liabilities)
        
        return jsonify({
            'success': True,
            'assets': assets,
            'liabilities': liabilities,
            'totalAssets': total_assets,
            'totalLiabilities': total_liabilities,
            'year': year,
            'date': date
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@clients_bp.route("/api/balance-sheet/<year>", methods=["PUT"])
@login_required
def save_balance_sheet(year):
    """Save balance sheet opening balances"""
    try:
        cid = session.get("company_id")
        data = request.get_json()
        updates = data.get('updates', [])
        
        for update in updates:
            account_id = update.get('account_id')
            field = update.get('field')
            value = update.get('value', 0)
            
            account = Account.query.filter_by(id=account_id, company_id=cid).first()
            if account:
                if field == 'opening_dr':
                    account.opening_dr = value
                elif field == 'opening_cr':
                    account.opening_cr = value
        
        db.session.commit()
        return jsonify({"success": True, "message": "Balance sheet saved successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@clients_bp.route("/clients/quick-add-item", methods=["POST"])
@login_required
def quick_add_item():
    try:
        from models import Item
        cid = session.get("company_id")
        name = request.form.get("name","").strip()
        if not name:
            return jsonify({"success": False, "error": "Item name required"}), 400
        
        item = Item(
            company_id=cid,
            name=name,
            hsn_code=request.form.get("hsn_code","").strip() or None,
            unit=request.form.get("unit","Nos"),
            gst_rate=float(request.form.get("gst_rate",18)),
            sale_rate=float(request.form.get("sale_rate",0)),
            purchase_rate=float(request.form.get("purchase_rate",0)),
            is_active=True
        )
        db.session.add(item)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "item": {
                "id": item.id,
                "name": item.name,
                "hsn_code": item.hsn_code or "",
                "unit": item.unit or "Nos",
                "gst_rate": float(item.gst_rate or 18),
                "sale_rate": float(item.sale_rate or 0),
                "purchase_rate": float(item.purchase_rate or 0)
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
