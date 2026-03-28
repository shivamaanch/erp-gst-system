import sqlite3
conn = sqlite3.connect('f:/erp/instance/erp.db')
c = conn.cursor()
# Add access for admin user to both companies
c.execute('INSERT INTO user_companies (user_id, company_id, role, is_active) VALUES (1, 1, "admin", 1)')
c.execute('INSERT INTO user_companies (user_id, company_id, role, is_active) VALUES (1, 2, "admin", 1)')
conn.commit()
print('Added admin access to both companies')
conn.close()
