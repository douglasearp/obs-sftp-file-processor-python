# API_USERS Table Documentation

## Overview

The `API_USERS` and `API_USER_ROLES` tables are used for JWT authentication in the OBS SFTP File Processor application.

## Table Creation

### Step 1: Create Tables

Run the table creation script:
```sql
@database/create_api_users_tables.sql
```

Or execute in your Oracle client:
```bash
sqlplus username/password@database < database/create_api_users_tables.sql
```

### Step 2: Insert Users

Run the user insertion script:
```sql
@database/insert_api_users_task_000006.sql
```

Or execute:
```bash
sqlplus username/password@database < database/insert_api_users_task_000006.sql
```

## Tables Created

### API_USERS

Stores user account information:
- `USER_ID` - Primary key (auto-generated)
- `USERNAME` - Unique username for login
- `PASSWORD_HASH` - Bcrypt hashed password
- `EMAIL` - User email address
- `FULL_NAME` - User's full name
- `IS_ACTIVE` - Account active status (1=active, 0=inactive)
- `IS_ADMIN` - Admin flag (1=admin, 0=user)
- `CREATED_DATE` - Account creation timestamp
- `LAST_LOGIN` - Last successful login timestamp
- `FAILED_LOGIN_ATTEMPTS` - Counter for failed login attempts
- `LOCKED_UNTIL` - Account lock expiration timestamp

### API_USER_ROLES

Stores user roles for role-based access control:
- `USER_ROLE_ID` - Primary key (auto-generated)
- `USER_ID` - Foreign key to API_USERS.USER_ID
- `ROLE_NAME` - Role name (e.g., ADMIN, USER)
- `CREATED_DATE` - Role assignment timestamp

## Users Created (Task-000006-Users)

### 1. douglasearp (Admin)
- **Username:** douglasearp
- **Password:** @Buttermilk1985!!
- **Email:** dearp@openbankingsolutions
- **Full Name:** Doug Earp
- **Is Admin:** Yes (1)
- **Role:** ADMIN

### 2. testuser (Regular User)
- **Username:** testuser
- **Password:** @SuperTester1985!!
- **Email:** testuser@openbankingsolutions
- **Full Name:** TestFname TestLname
- **Is Admin:** No (0)
- **Role:** USER

## Password Security

- Passwords are hashed using **bcrypt** with 12 rounds
- Never store plain text passwords
- Password hashes are stored in `PASSWORD_HASH` column
- Format: `$2b$12$...` (bcrypt with 12 rounds)

## Verification

To verify users were created correctly:

```sql
-- View all users
SELECT USERNAME, EMAIL, FULL_NAME, IS_ACTIVE, IS_ADMIN, CREATED_DATE
FROM API_USERS
ORDER BY USERNAME;

-- View users with their roles
SELECT 
    u.USERNAME,
    u.EMAIL,
    u.FULL_NAME,
    u.IS_ADMIN,
    r.ROLE_NAME,
    u.CREATED_DATE
FROM API_USERS u
LEFT JOIN API_USER_ROLES r ON u.USER_ID = r.USER_ID
ORDER BY u.USERNAME;
```

## Usage in Application

These users can be used for JWT authentication:
1. Login endpoint: `POST /auth/login` with username and password
2. Receive JWT tokens (access_token and refresh_token)
3. Use access_token in Authorization header: `Bearer <token>`
4. Access protected endpoints

## Security Notes

- Passwords are hashed with bcrypt (12 rounds)
- Account locking is supported via `FAILED_LOGIN_ATTEMPTS` and `LOCKED_UNTIL`
- Admin users have `IS_ADMIN = 1`
- Active status controlled by `IS_ACTIVE` flag

## Maintenance

### Reset Password
To reset a user's password, you'll need to:
1. Hash the new password using bcrypt
2. Update the `PASSWORD_HASH` column

### Disable User
```sql
UPDATE API_USERS 
SET IS_ACTIVE = 0 
WHERE USERNAME = 'username';
```

### Unlock Account
```sql
UPDATE API_USERS 
SET FAILED_LOGIN_ATTEMPTS = 0,
    LOCKED_UNTIL = NULL
WHERE USERNAME = 'username';
```

