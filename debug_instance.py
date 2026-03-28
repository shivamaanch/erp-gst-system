import sqlite3
db_path = 'f:/erp/instance/erp.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables:', [t[0] for t in tables])
print('\n=== Recent Bills (last 10) ===')
for row in c.execute('SELECT id, bill_no, bill_type, party_id, total_amount, bill_date, is_cancelled FROM bills ORDER BY id DESC LIMIT 10'):
    print(row)
print('\n=== Recent MilkTransactions (last 10) ===')
for row in c.execute('SELECT id, bill_id, txn_type, qty_liters, fat, snf, rate, amount, party_id, txn_date FROM milk_transactions ORDER BY id DESC LIMIT 10'):
    print(row)
conn.close()
