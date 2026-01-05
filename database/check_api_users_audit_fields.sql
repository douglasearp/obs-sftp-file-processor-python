-- Check if audit fields exist in API_USERS table
-- Run this query to see which audit fields are currently in the database

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

-- Expected results AFTER running alter_api_users_add_audit_fields.sql:
-- 
-- COLUMN_NAME        | DATA_TYPE | DATA_LENGTH | NULLABLE | DATA_DEFAULT
-- -------------------|-----------|-------------|----------|-------------
-- CREATED_BY_USER    | VARCHAR2  | 50          | Y        | NULL
-- CREATED_DATE       | TIMESTAMP | -           | N        | CURRENT_TIMESTAMP
-- UPDATED_BY_USER    | VARCHAR2  | 50          | Y        | NULL
-- UPDATED_DATE       | TIMESTAMP | -           | Y        | NULL
--
-- If you see fewer than 4 rows, the fields are missing and need to be added.

