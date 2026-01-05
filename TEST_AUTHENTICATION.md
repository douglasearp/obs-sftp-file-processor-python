# Testing Authentication

## Current Situation

The Docker container running on port 8001 is serving **old code** (2 weeks old) that doesn't have the new `/oracle-auth` endpoint with plain password support.

## To Test Authentication

### Step 1: Ensure User Exists in Database

Run the SQL script to create the admin user:
```bash
# Connect to Oracle database and run:
sqlplus username/password@database @database/insert_api_user_dearp_admin.sql
```

Or manually:
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

### Step 2: Update Docker Container

**Option A: Rebuild and Restart Docker Container**
```bash
cd /Users/dougearp/repos/obs-sftp-file-processor-python
docker-compose down
docker-compose up -d --build
```

**Option B: Use the Portainer Image**
The latest Portainer image (`obs-sftp-file-processor-portainer-v3.tar`) includes the new authentication code. Deploy it in Portainer.

### Step 3: Test Authentication

Once the container is updated, test with:

```bash
curl -X POST "http://localhost:8001/oracle-auth" \
  -H "Content-Type: application/json" \
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

### Test with Wrong Password

```bash
curl -X POST "http://localhost:8001/oracle-auth" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dearp@openbankingsolutions.com",
    "password": "wrongpassword"
  }'
```

**Expected Response:**
```json
{
  "authenticated": false,
  "is_admin": false
}
```

## User Credentials

- **Email:** `dearp@openbankingsolutions.com`
- **Password:** `@Buttermilk1985!!`
- **Username:** `dearp`
- **Admin:** Yes (IS_ADMIN = 1)
- **Active:** Yes (IS_ACTIVE = 1)

## Password Hash

The password `@Buttermilk1985!!` is hashed as:
```
$2b$12$HyRo2NsnVPk9raBPcYpGRODKMIn75e0AHV48/y8XP0fgRt8e1ZbCy
```

This hash is stored in the `PASSWORD_HASH` column in the `API_USERS` table.

