# Task-000008-AUTH: Oracle-Auth API Update

## Summary

Updated the `/oracle-auth` endpoint to return `authenticated` (true/false) and `is_admin` flag instead of just `result: 1/0`.

## API Changes

### Old Response Format
```json
{
  "result": 1  // 1 = match, 0 = no match
}
```

### New Response Format
```json
{
  "authenticated": true,  // true = match found, false = no match
  "is_admin": true        // true if user is admin (only when authenticated=true)
}
```

## Implementation Details

### 1. Updated Response Model (`models.py`)

**Before:**
```python
class OracleAuthResponse(BaseModel):
    result: int = Field(..., description="1 if match found, 0 if no match", ge=0, le=1)
```

**After:**
```python
class OracleAuthResponse(BaseModel):
    authenticated: bool = Field(..., description="True if email and password hash match, False otherwise")
    is_admin: bool = Field(False, description="True if user is admin, False otherwise (only set when authenticated=True)")
```

### 2. Updated Service Method (`oracle_service.py`)

**Before:**
- Returned: `bool` (True/False)
- Only checked if match existed

**After:**
- Returns: `Dict[str, Any]` with `authenticated` and `is_admin`
- Queries `IS_ADMIN` from `API_USERS` table
- Returns admin status when authenticated

**New Query:**
```sql
SELECT IS_ADMIN
FROM API_USERS
WHERE UPPER(EMAIL) = UPPER(:email)
  AND PASSWORD_HASH = :password_hash
  AND IS_ACTIVE = 1
```

### 3. Updated Endpoint (`main.py`)

**Before:**
```python
result = 1 if match_found else 0
return OracleAuthResponse(result=result)
```

**After:**
```python
auth_result = oracle_service.check_email_password_hash(...)
return OracleAuthResponse(
    authenticated=auth_result['authenticated'],
    is_admin=auth_result['is_admin']
)
```

## Response Examples

### Successful Authentication (Admin User)
```json
{
  "authenticated": true,
  "is_admin": true
}
```

### Successful Authentication (Regular User)
```json
{
  "authenticated": true,
  "is_admin": false
}
```

### Failed Authentication
```json
{
  "authenticated": false,
  "is_admin": false
}
```

## Next.js Integration

The `NEXTJS_ORACLE_AUTH_PLAN.md` has been updated with:
- New response interface
- Updated code examples (TypeScript & JavaScript)
- `is_admin` flag handling
- Role-based access control examples

## Usage in Frontend

```typescript
const response = await callOracleAuth(email, passwordHash);

if (response.authenticated) {
  // User is authenticated
  if (response.is_admin) {
    // Admin user - full access
    // Redirect to admin dashboard
  } else {
    // Regular user - limited access
    // Redirect to user dashboard
  }
} else {
  // Authentication failed
  showError('Invalid credentials');
}
```

## Files Modified

1. ✅ `src/obs_sftp_file_processor/models.py` - Updated `OracleAuthResponse`
2. ✅ `src/obs_sftp_file_processor/oracle_service.py` - Updated `check_email_password_hash()`
3. ✅ `src/obs_sftp_file_processor/main.py` - Updated `/oracle-auth` endpoint
4. ✅ `NEXTJS_ORACLE_AUTH_PLAN.md` - Updated Next.js integration plan

## Testing

### Test with Admin User
```bash
curl -X POST "http://localhost:8002/oracle-auth" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dearp@openbankingsolutions",
    "password_hash": "$2b$12$HyRo2NsnVPk9raBPcYpGRODKMIn75e0AHV48/y8XP0fgRt8e1ZbCy"
  }'
```

**Expected Response:**
```json
{
  "authenticated": true,
  "is_admin": true
}
```

### Test with Regular User
```bash
curl -X POST "http://localhost:8002/oracle-auth" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@openbankingsolutions",
    "password_hash": "$2b$12$df1XXbWyEPc0lG/c8djPs.8.Kb2Bi53bbabs7g5D9PZC7P8q70GYe"
  }'
```

**Expected Response:**
```json
{
  "authenticated": true,
  "is_admin": false
}
```

## Status

✅ **Complete** - API updated and Next.js plan updated

