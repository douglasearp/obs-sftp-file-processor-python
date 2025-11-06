# JWT Authentication Implementation Plan

This document outlines the plan to add JWT (JSON Web Token) authentication to secure the FastAPI APIs in the OBS SFTP File Processor application.

## 📋 Overview

**Goal:** Add JWT-based authentication to protect all API endpoints except health checks, ensuring only authenticated users can access sensitive operations.

**Approach:** Use `python-jose` library with FastAPI's built-in security features to implement JWT token-based authentication.

---

## 🎯 Current API Endpoints Analysis

### **Public Endpoints (No Authentication Required)**
These should remain accessible without authentication:
- `GET /` - Health check
- `GET /health` - Detailed health check
- `POST /auth/login` - **NEW** - User login endpoint (creates JWT)
- `POST /auth/refresh` - **NEW** - Refresh JWT token

### **Protected Endpoints (Require JWT Authentication)**
All other endpoints should require a valid JWT token:

#### SFTP Endpoints:
- `GET /files` - List files
- `GET /files/search/{file_name}` - Search files
- `GET /file/{file_name}` - Get file by name
- `GET /files/{file_path:path}` - Read file by path
- `POST /files/addsftpachfile` - Upload ACH file to SFTP

#### Oracle Database Endpoints:
- `GET /oracle/ach-files` - List ACH files
- `GET /oracle/ach-files/{file_id}` - Get specific ACH file
- `POST /oracle/ach-files` - Create ACH file
- `PUT /oracle/ach-files/{file_id}` - Update ACH file
- `POST /oracle/ach-files-update-by-file-id/{file_id}` - Update by file ID
- `DELETE /oracle/ach-files/{file_id}` - Delete ACH file
- `GET /oracle/clients` - Get active clients

#### Sync Endpoints:
- `POST /sync/sftp-to-oracle` - Sync SFTP to Oracle
- `POST /run-sync-process` - Run complete sync process

---

## 📦 Required Dependencies

### **New Python Packages to Install:**
```bash
uv add python-jose[cryptography] passlib[bcrypt] python-multipart
```

**Package Details:**
- `python-jose[cryptography]` - JWT encoding/decoding with cryptographic support
- `passlib[bcrypt]` - Password hashing (if storing user credentials)
- `python-multipart` - Required for FastAPI OAuth2PasswordBearer (form data)

### **Optional Dependencies:**
- `python-jose[all]` - Includes all algorithms (alternative to [cryptography])

---

## 🏗️ Architecture Components to Create

### **1. Authentication Configuration (`src/obs_sftp_file_processor/auth_config.py`)**
**Purpose:** Store JWT configuration settings

**Configuration Values Needed:**
- `JWT_SECRET_KEY` - Secret key for signing tokens (from environment variable)
- `JWT_ALGORITHM` - Algorithm (e.g., "HS256")
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time (default: 30 minutes)
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token expiration (default: 7 days)
- `JWT_TOKEN_PREFIX` - Token prefix in Authorization header (default: "Bearer")

**Environment Variables:**
```env
JWT_SECRET_KEY=your-secret-key-here-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

### **2. User Models (`src/obs_sftp_file_processor/auth_models.py`)**
**Purpose:** Define Pydantic models for authentication

**Models to Create:**
- `UserLogin` - Request model for login (username, password)
- `TokenResponse` - Response model for JWT tokens (access_token, refresh_token, token_type)
- `TokenData` - Internal model for token payload (username, exp, etc.)
- `User` - User model (username, email, disabled, etc.) - Optional if storing users in DB

**Example Structure:**
```python
class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None
    exp: Optional[int] = None
```

---

### **3. User Service (`src/obs_sftp_file_processor/user_service.py`)**
**Purpose:** Handle user authentication and validation

**Initial Approach Options:**

#### **Option A: Simple In-Memory Users (Quick Start)**
- Store users in a Python dictionary or config file
- Good for development/testing
- Simple password hashing with passlib

#### **Option B: Oracle Database Users Table (Recommended)**
- Create `API_USERS` table in Oracle
- Store username, hashed password, email, roles, etc.
- More secure and scalable
- Integrates with existing Oracle infrastructure

#### **Option C: LDAP/Active Directory Integration (Enterprise)**
- Connect to existing LDAP/AD
- No local user storage needed
- Best for enterprise environments

**Functions to Implement:**
- `authenticate_user(username, password)` - Verify credentials
- `get_user(username)` - Retrieve user by username
- `create_user(username, password, email)` - **Optional** - Create new users
- `hash_password(password)` - Hash passwords with bcrypt
- `verify_password(plain_password, hashed_password)` - Verify passwords

**Recommendation:** Start with **Option B (Oracle Database)** to leverage existing Oracle infrastructure.

---

### **4. JWT Service (`src/obs_sftp_file_processor/jwt_service.py`)**
**Purpose:** Handle JWT token creation, validation, and refresh

**Functions to Implement:**
- `create_access_token(data: dict, expires_delta: Optional[timedelta])` - Create JWT token
- `create_refresh_token(data: dict)` - Create refresh token
- `decode_token(token: str)` - Decode and validate JWT token
- `verify_token(token: str)` - Verify token signature and expiration
- `get_current_user(token: str)` - Extract user from token

**Token Payload Structure:**
```json
{
  "sub": "username",
  "exp": 1234567890,
  "iat": 1234567890,
  "type": "access" | "refresh"
}
```

---

### **5. Authentication Dependencies (`src/obs_sftp_file_processor/auth_dependencies.py`)**
**Purpose:** FastAPI dependencies for protecting endpoints

**Dependencies to Create:**
- `get_current_user()` - FastAPI dependency that extracts and validates JWT
- `get_current_active_user()` - Dependency that ensures user is active
- `oauth2_scheme` - OAuth2PasswordBearer instance for token extraction

**Usage Pattern:**
```python
@app.get("/protected-endpoint")
async def protected_endpoint(
    current_user: User = Depends(get_current_active_user)
):
    # Endpoint logic here
    pass
```

---

### **6. Authentication Routes (`src/obs_sftp_file_processor/auth_routes.py`)**
**Purpose:** Authentication endpoints (login, refresh, logout)

**Endpoints to Create:**
- `POST /auth/login` - Authenticate user and return JWT tokens
- `POST /auth/refresh` - Refresh access token using refresh token
- `POST /auth/logout` - **Optional** - Invalidate token (requires token blacklist)
- `GET /auth/me` - **Optional** - Get current user info

**Response Format:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 🔧 Configuration Changes

### **1. Update `src/obs_sftp_file_processor/config.py`**
**Changes Needed:**
- Add `AuthConfig` class for JWT settings
- Integrate `AuthConfig` into `AppConfig`
- Add JWT configuration to environment variable loading

### **2. Update `env.example`**
**Add New Environment Variables:**
```env
# JWT Authentication
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### **3. Update `docker-compose.yml`**
**Add JWT Environment Variables:**
```yaml
environment:
  - JWT_SECRET_KEY=${JWT_SECRET_KEY}
  - JWT_ALGORITHM=${JWT_ALGORITHM:-HS256}
  - JWT_ACCESS_TOKEN_EXPIRE_MINUTES=${JWT_ACCESS_TOKEN_EXPIRE_MINUTES:-30}
```

---

## 📝 Database Schema Changes (If Using Oracle)

### **Option: Create API_USERS Table**
```sql
CREATE TABLE API_USERS (
    USER_ID NUMBER(38,0) GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    USERNAME VARCHAR2(50) NOT NULL UNIQUE,
    PASSWORD_HASH VARCHAR2(255) NOT NULL,
    EMAIL VARCHAR2(100),
    FULL_NAME VARCHAR2(100),
    IS_ACTIVE NUMBER(1) DEFAULT 1 NOT NULL,
    IS_ADMIN NUMBER(1) DEFAULT 0 NOT NULL,
    CREATED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    LAST_LOGIN TIMESTAMP,
    FAILED_LOGIN_ATTEMPTS NUMBER(3) DEFAULT 0,
    LOCKED_UNTIL TIMESTAMP
);

CREATE INDEX IDX_API_USERS_USERNAME ON API_USERS(USERNAME);
CREATE INDEX IDX_API_USERS_EMAIL ON API_USERS(EMAIL);
```

**Optional: Add Roles Table**
```sql
CREATE TABLE API_USER_ROLES (
    USER_ROLE_ID NUMBER(38,0) GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    USER_ID NUMBER(38,0) NOT NULL,
    ROLE_NAME VARCHAR2(50) NOT NULL,
    FOREIGN KEY (USER_ID) REFERENCES API_USERS(USER_ID)
);
```

---

## 🔒 Security Considerations

### **1. Token Storage**
- **Access Tokens:** Short-lived (30 minutes), stored in memory (client-side)
- **Refresh Tokens:** Long-lived (7 days), stored securely (httpOnly cookie recommended)
- **Token Blacklist:** Optional - for logout functionality (requires Redis or database)

### **2. Password Security**
- Use `passlib[bcrypt]` for password hashing
- Minimum 12 rounds of bcrypt
- Never store plain text passwords
- Enforce password complexity rules (optional)

### **3. Secret Key Management**
- Generate strong secret key (minimum 32 characters)
- Store in environment variables, never in code
- Use different keys for development/production
- Consider using key rotation strategy

### **4. HTTPS/TLS**
- **REQUIRED** for production (JWT tokens in HTTP headers are vulnerable over HTTP)
- Use reverse proxy (nginx, Traefik) with SSL certificates
- Configure Portainer with HTTPS

### **5. Rate Limiting** (Optional but Recommended)
- Limit login attempts (e.g., 5 attempts per 15 minutes)
- Prevent brute force attacks
- Track failed login attempts in database

### **6. CORS Configuration**
- Configure CORS properly for frontend applications
- Only allow trusted origins
- Set appropriate headers

---

## 🧪 Testing Strategy

### **1. Unit Tests**
- `test_jwt_service.py` - Test JWT token creation/validation
- `test_user_service.py` - Test user authentication
- `test_auth_dependencies.py` - Test authentication dependencies

### **2. Integration Tests**
- `test_auth_endpoints.py` - Test login/refresh endpoints
- `test_protected_endpoints.py` - Test protected endpoints with/without tokens
- `test_token_expiration.py` - Test token expiration handling

### **3. Test Scenarios**
- ✅ Valid login returns tokens
- ✅ Invalid credentials return 401
- ✅ Protected endpoint without token returns 401
- ✅ Protected endpoint with valid token works
- ✅ Protected endpoint with expired token returns 401
- ✅ Refresh token works
- ✅ Multiple concurrent requests with same token
- ✅ Token with invalid signature returns 401

---

## 📋 Implementation Steps (Order of Execution)

### **Phase 1: Foundation Setup**
1. ✅ Install required dependencies (`python-jose`, `passlib`, `python-multipart`)
2. ✅ Create `auth_config.py` with JWT configuration
3. ✅ Update `config.py` to include auth config
4. ✅ Add JWT environment variables to `env.example`

### **Phase 2: Core Authentication Components**
5. ✅ Create `auth_models.py` with Pydantic models
6. ✅ Create `jwt_service.py` with JWT functions
7. ✅ Create `user_service.py` with user authentication logic
8. ✅ Create `auth_dependencies.py` with FastAPI dependencies

### **Phase 3: Database Integration (If Using Oracle)**
9. ✅ Create Oracle `API_USERS` table schema
10. ✅ Add user service methods to interact with Oracle
11. ✅ Create initial admin user (or seed script)

### **Phase 4: Authentication Endpoints**
12. ✅ Create `auth_routes.py` with login/refresh endpoints
13. ✅ Register auth routes in `main.py`
14. ✅ Test login endpoint

### **Phase 5: Protect Existing Endpoints**
15. ✅ Add `Depends(get_current_active_user)` to all protected endpoints
16. ✅ Keep health check endpoints public
17. ✅ Update endpoint documentation

### **Phase 6: Testing & Validation**
18. ✅ Write unit tests for JWT service
19. ✅ Write integration tests for auth endpoints
20. ✅ Test all protected endpoints with valid tokens
21. ✅ Test error scenarios (expired tokens, invalid tokens)

### **Phase 7: Documentation & Deployment**
22. ✅ Update API documentation with authentication info
23. ✅ Update README.md with authentication setup
24. ✅ Update `docker-compose.yml` with JWT env vars
25. ✅ Create migration guide for existing API consumers

---

## 🔄 Migration Strategy

### **For Existing API Consumers:**

1. **Backward Compatibility Period (Optional):**
   - Add feature flag to enable/disable authentication
   - Allow gradual migration
   - Log warnings for unauthenticated requests

2. **Communication:**
   - Notify API consumers of authentication requirement
   - Provide API keys or user accounts
   - Share updated API documentation

3. **Breaking Changes:**
   - All protected endpoints will return 401 without valid token
   - Health checks remain public
   - Update all API clients to include Authorization header

---

## 📚 API Usage Examples (After Implementation)

### **Login:**
```bash
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret"}'
```

### **Use Token:**
```bash
curl -X GET "http://localhost:8001/oracle/ach-files" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### **Refresh Token:**
```bash
curl -X POST "http://localhost:8001/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIs..."}'
```

---

## 🎛️ Configuration Recommendations

### **Development:**
- Short token expiration (15 minutes) for testing
- Simple secret key (not production-grade)
- Verbose error messages

### **Production:**
- Longer token expiration (30-60 minutes)
- Strong secret key (32+ characters, randomly generated)
- Generic error messages (don't reveal user existence)
- Rate limiting on login endpoint
- Token blacklist for logout (optional)

---

## ⚠️ Important Notes

1. **Secret Key Security:**
   - NEVER commit secret keys to git
   - Use environment variables or secret management
   - Generate strong random keys for production

2. **Token Expiration:**
   - Balance security (shorter) vs. user experience (longer)
   - Use refresh tokens for better UX
   - Consider "remember me" functionality

3. **User Management:**
   - Decide on user creation process (admin-only, self-registration, etc.)
   - Consider password reset functionality
   - Plan for user role management (admin, user, read-only, etc.)

4. **Error Handling:**
   - Return 401 for authentication failures
   - Return 403 for authorization failures (if implementing roles)
   - Provide clear error messages without revealing security details

5. **Performance:**
   - JWT validation is fast (no database lookup needed)
   - Consider caching user data if needed
   - Monitor token validation performance

---

## 📖 Additional Resources

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [python-jose Documentation](https://python-jose.readthedocs.io/)
- [JWT.io - JWT Debugger](https://jwt.io/)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)

---

## ✅ Success Criteria

The implementation is complete when:
- ✅ All protected endpoints require valid JWT token
- ✅ Health check endpoints remain public
- ✅ Login endpoint returns valid JWT tokens
- ✅ Refresh token endpoint works correctly
- ✅ Expired tokens are rejected
- ✅ Invalid tokens are rejected
- ✅ All tests pass
- ✅ Documentation is updated
- ✅ Docker deployment includes JWT configuration

---

## 📝 Next Steps

**When you're ready to implement:**
1. Review this plan and confirm approach
2. Decide on user storage (Oracle DB recommended)
3. Generate a strong JWT secret key
4. Start with Phase 1 (Foundation Setup)
5. Test incrementally as you build each phase

**Questions to Answer Before Implementation:**
- Where will users be stored? (Oracle DB, in-memory, LDAP?)
- Who can create users? (Admin only, self-registration?)
- What roles/permissions are needed? (Admin, User, Read-only?)
- Should logout invalidate tokens? (Requires token blacklist)
- What's the token expiration policy? (30 min access, 7 day refresh?)

