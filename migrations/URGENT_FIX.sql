-- URGENT FIX: Run this SQL directly in Northflank PostgreSQL console
-- This adds the missing columns that are preventing the app from starting

-- Add is_active column to companies table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'companies' AND column_name = 'is_active'
    ) THEN
        ALTER TABLE companies ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
        UPDATE companies SET is_active = TRUE WHERE is_active IS NULL;
        RAISE NOTICE 'Added is_active column to companies table';
    ELSE
        RAISE NOTICE 'is_active column already exists in companies table';
    END IF;
END $$;

-- Add account_id column to cash_book table
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cash_book' AND column_name = 'account_id'
    ) THEN
        ALTER TABLE cash_book ADD COLUMN account_id INTEGER;
        RAISE NOTICE 'Added account_id column to cash_book table';
    ELSE
        RAISE NOTICE 'account_id column already exists in cash_book table';
    END IF;
END $$;

-- Verify the fixes
SELECT 'companies.is_active' as column_check, 
       CASE WHEN EXISTS (
           SELECT 1 FROM information_schema.columns 
           WHERE table_name = 'companies' AND column_name = 'is_active'
       ) THEN 'EXISTS ✓' ELSE 'MISSING ✗' END as status
UNION ALL
SELECT 'cash_book.account_id' as column_check,
       CASE WHEN EXISTS (
           SELECT 1 FROM information_schema.columns 
           WHERE table_name = 'cash_book' AND column_name = 'account_id'
       ) THEN 'EXISTS ✓' ELSE 'MISSING ✗' END as status;
