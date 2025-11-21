# Task-000007: Oracle Auth API Implementation

## Overview

Created the `/oracle-auth` API endpoint that checks if an email and password hash match in the `API_USERS` table, with rate limiting of 15 requests per minute per email.

## Implementation Details

### Endpoint

**POST** `/oracle-auth`

### Request Model

```json
{
  "email": "user@example.com",
  "password_hash": "$2b$12$..."
}
```

### Response Model

```json
{
  "result": 1  // 1 for match, 0 for no match
}
```

### Rate Limiting

- **Limit:** 15 requests per minute per email
- **Window:** 60 seconds (1 minute)
- **Response:** HTTP 429 (Too Many Requests) if limit exceeded

## Files Created/Modified

### 1. `src/obs_sftp_file_processor/models.py`
- Added `OracleAuthRequest` model
- Added `OracleAuthResponse` model

### 2. `src/obs_sftp_file_processor/rate_limiter.py` (NEW)
- Created `RateLimiter` class for in-memory rate limiting
- Global instance: `oracle_auth_rate_limiter` (15 requests/minute)

### 3. `src/obs_sftp_file_processor/oracle_service.py`
- Added `check_email_password_hash()` method
- Queries `API_USERS` table for matching email and password_hash
- Only checks active users (`IS_ACTIVE = 1`)

### 4. `src/obs_sftp_file_processor/main.py`
- Added `/oracle-auth` POST endpoint
- Integrated rate limiting
- Returns 1 for match, 0 for no match

## Database Query

The endpoint queries the `API_USERS` table:

```sql
SELECT COUNT(*) 
FROM API_USERS
WHERE UPPER(EMAIL) = UPPER(:email)
  AND PASSWORD_HASH = :password_hash
  AND IS_ACTIVE = 1
```

- Case-insensitive email matching
- Exact password hash match
- Only active users (`IS_ACTIVE = 1`)

## Usage Examples

### Successful Match (Returns 1)

```bash
curl -X POST "http://localhost:8001/oracle-auth" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dearp@openbankingsolutions",
    "password_hash": "$2b$12$HyRo2NsnVPk9raBPcYpGRODKMIn75e0AHV48/y8XP0fgRt8e1ZbCy"
  }'
```

**Response:**
```json
{
  "result": 1
}
```

### No Match (Returns 0)

```bash
curl -X POST "http://localhost:8001/oracle-auth" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dearp@openbankingsolutions",
    "password_hash": "$2b$12$invalidhash..."
  }'
```

**Response:**
```json
{
  "result": 0
}
```

### Rate Limit Exceeded (HTTP 429)

After 15 requests in 1 minute for the same email:

```json
{
  "detail": "Rate limit exceeded. Maximum 15 requests per minute per email. Please try again later."
}
```

## Rate Limiting Details

- **Storage:** In-memory (resets on application restart)
- **Tracking:** Per email address
- **Window:** Sliding 60-second window
- **Cleanup:** Automatic cleanup of old requests outside the window

### Rate Limiter Behavior

1. Tracks request timestamps per email
2. Removes requests older than 60 seconds
3. Checks if count >= 15
4. If limit exceeded, returns HTTP 429
5. If allowed, adds current request timestamp

## Security Considerations

1. **Password Hash Verification:** Only checks exact hash matches
2. **Case-Insensitive Email:** Email matching is case-insensitive
3. **Active Users Only:** Only checks users with `IS_ACTIVE = 1`
4. **Rate Limiting:** Prevents brute force attacks (15 requests/minute)
5. **No Plain Text:** Only accepts password hashes, not plain passwords

## Error Handling

- **Rate Limit Exceeded:** HTTP 429 with descriptive message
- **Database Error:** HTTP 500 with error details
- **Invalid Request:** HTTP 422 (FastAPI validation)

## Testing

### Test Cases

1. ✅ Valid email and password hash → Returns 1
2. ✅ Valid email, invalid password hash → Returns 0
3. ✅ Invalid email → Returns 0
4. ✅ Rate limit exceeded → HTTP 429
5. ✅ Case-insensitive email matching
6. ✅ Only active users checked

### Manual Testing

```bash
# Test 1: Valid credentials
curl -X POST "http://localhost:8001/oracle-auth" \
  -H "Content-Type: application/json" \
  -d '{"email": "dearp@openbankingsolutions", "password_hash": "$2b$12$HyRo2NsnVPk9raBPcYpGRODKMIn75e0AHV48/y8XP0fgRt8e1ZbCy"}'

# Test 2: Invalid password hash
curl -X POST "http://localhost:8001/oracle-auth" \
  -H "Content-Type: application/json" \
  -d '{"email": "dearp@openbankingsolutions", "password_hash": "invalid"}'

# Test 3: Rate limit (run 16 times quickly)
for i in {1..16}; do
  curl -X POST "http://localhost:8001/oracle-auth" \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password_hash": "test"}'
  echo ""
done
```

## API Documentation

The endpoint is automatically documented in FastAPI's Swagger UI:
- **URL:** `http://localhost:8001/docs`
- **Endpoint:** `POST /oracle-auth`
- **Schema:** Available in Swagger UI

## Notes

- Rate limiting is in-memory and resets on application restart
- For production, consider using Redis or database-backed rate limiting
- Password hash must match exactly (case-sensitive)
- Email matching is case-insensitive
- Only active users are checked

## Status

✅ **Complete** - Endpoint implemented and ready for use

