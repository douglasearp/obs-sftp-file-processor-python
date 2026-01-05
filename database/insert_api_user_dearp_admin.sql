-- Insert admin user: dearp@openbankingsolutions.com
-- Password: @Buttermilk1985!!
-- Note: Ensure API_USERS table exists before running this script
-- Run: database/create_api_users_tables.sql first if table doesn't exist

-- ============================================
-- User: dearp@openbankingsolutions.com (Admin)
-- ============================================
-- First, check if user already exists and delete if present
DELETE FROM API_USERS WHERE UPPER(EMAIL) = UPPER('dearp@openbankingsolutions.com');

-- Insert the admin user
INSERT INTO API_USERS (
    USERNAME,
    PASSWORD_HASH,
    EMAIL,
    FULL_NAME,
    IS_ACTIVE,
    IS_ADMIN,
    CREATED_DATE
) VALUES (
    'dearp',
    '$2b$12$HyRo2NsnVPk9raBPcYpGRODKMIn75e0AHV48/y8XP0fgRt8e1ZbCy',  -- @Buttermilk1985!!
    'dearp@openbankingsolutions.com',
    'Doug Earp',
    1,  -- IS_ACTIVE
    1,  -- IS_ADMIN
    CURRENT_TIMESTAMP
);

-- Verify the user was created
SELECT 
    USER_ID,
    USERNAME,
    EMAIL,
    FULL_NAME,
    IS_ACTIVE,
    IS_ADMIN,
    CREATED_DATE
FROM API_USERS
WHERE UPPER(EMAIL) = UPPER('dearp@openbankingsolutions.com');

-- Expected output:
-- USER_ID | USERNAME | EMAIL                              | FULL_NAME | IS_ACTIVE | IS_ADMIN | CREATED_DATE
-- --------|----------|------------------------------------|-----------|-----------|----------|-------------
-- 1       | dearp    | dearp@openbankingsolutions.com    | Doug Earp | 1         | 1        | [timestamp]

