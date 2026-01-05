# Fix Authentication Issue

## Problem

The authentication is failing because:

1. **Password Mismatch**: You're testing with `"Buttermilk1985!!"` but the password hash in the database is for `"@Buttermilk1985!!"` (with @ symbol at the beginning)

2. **User May Not Exist**: The user needs to be created in the database first

## Solution

### Step 1: Create the User in Database

Run the SQL script to create the user:

```bash
# Connect to Oracle and run:
sqlplus username/password@database @database/insert_api_user_dearp_admin.sql
```

Or manually execute:

```sql
DELETE FROM API_USERS WHERE UPPER(EMAIL) = UPPER('dearp@openbankingsolutions.com');

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
    '$2b$12$HyRo2NsnVPk9raBPcYpGRODKMIn75e0AHV48/y8XP0fgRt8e1ZbCy',
    'dearp@openbankingsolutions.com',
    'Doug Earp',
    1,
    1,
    CURRENT_TIMESTAMP
);
```

### Step 2: Use Correct Password

**Correct password:** `@Buttermilk1985!!` (with @ symbol)

**Incorrect password:** `Buttermilk1985!!` (without @ symbol)

### Step 3: Test with Correct Password

```bash
curl -X POST 'http://localhost:8001/oracle-auth' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "dearp@openbankingsolutions.com",
  "password": "@Buttermilk1985!!"
}'
```

**Expected Response:**
```json
{
  "authenticated": true,
  "is_admin": true
}
```

## Alternative: Create User with Different Password

If you want to use `"Buttermilk1985!!"` (without @), you need to:

1. Generate a new hash for that password
2. Update the database with the new hash

But the existing hash in the database is for `"@Buttermilk1985!!"`, so you should use that password.

## Note About Bcrypt Warning

The logs show a bcrypt version compatibility warning, but this doesn't prevent authentication from working. The actual issue is the password mismatch.

