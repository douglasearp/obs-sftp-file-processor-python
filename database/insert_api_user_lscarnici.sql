-- Insert user lscarnici for API_USERS table
-- This script creates user: lscarnici (admin)
-- Note: Ensure API_USERS and API_USER_ROLES tables exist before running this script
-- Run: database/create_api_users_tables.sql first if tables don't exist

-- ============================================
-- User: lscarnici (Admin)
-- ============================================
INSERT INTO API_USERS (
    USERNAME,
    PASSWORD_HASH,
    EMAIL,
    FULL_NAME,
    IS_ACTIVE,
    IS_ADMIN,
    CREATED_DATE
) VALUES (
    'lscarnici',
    '$2b$12$XOH/GqyaSn7bdD/WQOjrIegiuDToXp8BcydQHpCzICoBnsqxbYKBS',  -- @SuperBanker8675309!!
    'lscarnici@openbankingsolutions.com',
    'Lisa Scarnici',
    1,  -- IS_ACTIVE
    1,  -- IS_ADMIN
    CURRENT_TIMESTAMP
);

-- Create ADMIN role for lscarnici
INSERT INTO API_USER_ROLES (
    USER_ID,
    ROLE_NAME,
    CREATED_DATE
) VALUES (
    (SELECT USER_ID FROM API_USERS WHERE USERNAME = 'lscarnici'),
    'ADMIN',
    CURRENT_TIMESTAMP
);

-- ============================================
-- Verification Queries
-- ============================================
-- Uncomment to verify the inserts:

-- SELECT * FROM API_USERS WHERE USERNAME = 'lscarnici';
-- SELECT u.USERNAME, u.EMAIL, u.FULL_NAME, u.IS_ADMIN, r.ROLE_NAME 
-- FROM API_USERS u
-- LEFT JOIN API_USER_ROLES r ON u.USER_ID = r.USER_ID
-- WHERE u.USERNAME = 'lscarnici';

COMMIT;

