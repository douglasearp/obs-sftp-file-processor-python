-- Insert users for Task-000006-Users
-- This script creates two users: douglasearp (admin) and testuser (regular user)
-- Note: Ensure API_USERS and API_USER_ROLES tables exist before running this script
-- Run: database/create_api_users_tables.sql first if tables don't exist

-- ============================================
-- User 1: douglasearp (Admin)
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
    'douglasearp',
    '$2b$12$HyRo2NsnVPk9raBPcYpGRODKMIn75e0AHV48/y8XP0fgRt8e1ZbCy',  -- @Buttermilk1985!!
    'dearp@openbankingsolutions',
    'Doug Earp',
    1,  -- IS_ACTIVE
    1,  -- IS_ADMIN
    CURRENT_TIMESTAMP
);

-- Get the USER_ID for douglasearp to create role
-- Note: In Oracle, we can use RETURNING clause or query the sequence
-- For simplicity, we'll use a subquery to get the USER_ID

INSERT INTO API_USER_ROLES (
    USER_ID,
    ROLE_NAME,
    CREATED_DATE
) VALUES (
    (SELECT USER_ID FROM API_USERS WHERE USERNAME = 'douglasearp'),
    'ADMIN',
    CURRENT_TIMESTAMP
);

-- ============================================
-- User 2: testuser (Regular User)
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
    'testuser',
    '$2b$12$df1XXbWyEPc0lG/c8djPs.8.Kb2Bi53bbabs7g5D9PZC7P8q70GYe',  -- @SuperTester1985!!
    'testuser@openbankingsolutions',
    'TestFname TestLname',
    1,  -- IS_ACTIVE
    0,  -- IS_ADMIN (not admin)
    CURRENT_TIMESTAMP
);

-- Create role for testuser
INSERT INTO API_USER_ROLES (
    USER_ID,
    ROLE_NAME,
    CREATED_DATE
) VALUES (
    (SELECT USER_ID FROM API_USERS WHERE USERNAME = 'testuser'),
    'USER',
    CURRENT_TIMESTAMP
);

-- ============================================
-- Verification Queries
-- ============================================
-- Uncomment to verify the inserts:

-- SELECT * FROM API_USERS;
-- SELECT u.USERNAME, u.EMAIL, u.FULL_NAME, u.IS_ADMIN, r.ROLE_NAME 
-- FROM API_USERS u
-- LEFT JOIN API_USER_ROLES r ON u.USER_ID = r.USER_ID
-- ORDER BY u.USERNAME;

COMMIT;

