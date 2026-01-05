-- Add audit fields to API_USERS table
-- This script adds CREATED_BY_USER, UPDATED_BY_USER, and UPDATED_DATE columns
-- CREATED_DATE already exists in the table

-- Note: If columns already exist, these statements will fail gracefully
-- You can check for existing columns first if needed:
-- SELECT COLUMN_NAME FROM USER_TAB_COLUMNS WHERE TABLE_NAME = 'API_USERS' AND COLUMN_NAME IN ('CREATED_BY_USER', 'UPDATED_BY_USER', 'UPDATED_DATE');

-- Add CREATED_BY_USER column
ALTER TABLE API_USERS
ADD CREATED_BY_USER VARCHAR2(50);

-- Add UPDATED_BY_USER column
ALTER TABLE API_USERS
ADD UPDATED_BY_USER VARCHAR2(50);

-- Add UPDATED_DATE column
ALTER TABLE API_USERS
ADD UPDATED_DATE TIMESTAMP;

-- Add comments for documentation
COMMENT ON COLUMN API_USERS.CREATED_BY_USER IS 'User who created the record';
COMMENT ON COLUMN API_USERS.UPDATED_BY_USER IS 'User who last updated the record';
COMMENT ON COLUMN API_USERS.UPDATED_DATE IS 'Timestamp when record was last updated';

-- Optional: Add indexes for better query performance
-- Uncomment if you need to query by these fields frequently

-- CREATE INDEX IDX_API_USERS_CREATED_BY_USER ON API_USERS(CREATED_BY_USER);
-- CREATE INDEX IDX_API_USERS_UPDATED_BY_USER ON API_USERS(UPDATED_BY_USER);
-- CREATE INDEX IDX_API_USERS_UPDATED_DATE ON API_USERS(UPDATED_DATE);

-- Verify the changes
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    DATA_LENGTH,
    NULLABLE,
    DATA_DEFAULT
FROM USER_TAB_COLUMNS
WHERE TABLE_NAME = 'API_USERS'
  AND COLUMN_NAME IN ('CREATED_BY_USER', 'CREATED_DATE', 'UPDATED_BY_USER', 'UPDATED_DATE')
ORDER BY COLUMN_NAME;

-- Expected output after running:
-- COLUMN_NAME        | DATA_TYPE | DATA_LENGTH | NULLABLE | DATA_DEFAULT
-- -------------------|-----------|-------------|----------|-------------
-- CREATED_BY_USER    | VARCHAR2  | 50          | Y        | NULL
-- CREATED_DATE       | TIMESTAMP | -           | N        | CURRENT_TIMESTAMP
-- UPDATED_BY_USER    | VARCHAR2  | 50          | Y        | NULL
-- UPDATED_DATE       | TIMESTAMP | -           | Y        | NULL

