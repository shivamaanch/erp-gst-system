#!/bin/bash
# SQL Database Fix Script

echo "Starting SQL database fix..."

# Try to connect and run SQL
echo "Attempting to add voucher_no columns..."

# Method 1: Try Python first
python run_db_fix.py

# Method 2: Direct SQL if Python fails
if [ $? -ne 0 ]; then
    echo "Python fix failed, trying direct SQL..."
    
    # Try to find PostgreSQL connection details
    if [ -f ".env" ]; then
        echo "Found .env file, checking for database URL..."
        grep -i DATABASE_URL .env
    fi
    
    echo "Running SQL commands..."
    echo "ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50);"
    echo "ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50);"
    
    # Try to run SQL with psql
    command -v psql --help >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "psql found, trying direct SQL..."
        psql -h localhost -U postgres -d erp -c "ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50);" || echo "psql bills failed"
        psql -h localhost -U postgres -d erp -c "ALTER TABLE milk_transactions ADD COLUMN voucher_no VARCHAR(50);" || echo "psql milk_transactions failed"
    else
        echo "psql not found, trying other methods..."
        echo "Please install PostgreSQL client: apt-get install postgresql-client"
        echo "Then run: psql -h localhost -U postgres -d erp -c "ALTER TABLE bills ADD COLUMN voucher_no VARCHAR(50);""
    fi
fi

echo "SQL fix attempt completed!"
