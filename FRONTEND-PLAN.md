# Frontend Authentication Plan - Updated API (Task-000019)

## Overview

The backend authentication API has been **refactored** to accept **plain text passwords** instead of password hashes. This simplifies the frontend implementation significantly - **no password hashing is required on the client side**.

**Key Change:** The backend now uses `bcrypt.verify()` to securely compare the plain password against the stored hash in the database.

---

## What Changed in the Backend

### Before (Old Implementation)
- Frontend had to hash passwords using bcrypt (12 rounds)
- Frontend sent `password_hash` to backend
- Backend compared hash-to-hash (insecure pattern)

### After (New Implementation - Current)
- Frontend sends **plain password** over HTTPS
- Backend uses `bcrypt.verify()` to check password against stored hash
- Standard, secure authentication pattern

---

## Backend API Endpoint

### Endpoint Information
- **URL:** `POST /oracle-auth`
- **Base URL:** `http://localhost:8001` (local) or your production API URL
- **Content-Type:** `application/json`
- **Rate Limit:** 15 requests per minute per email

### Request Format (NEW)
```json
{
  "email": "user@example.com",
  "password": "@Buttermilk1985!!"  // Plain text password (NOT hashed)
}
```

### Response Format
```json
{
  "authenticated": true,  // true = password matches, false = no match
  "is_admin": true        // true if user is admin (only set when authenticated=true)
}
```

### Error Responses
- **429 Too Many Requests:** Rate limit exceeded (15 requests/minute per email)
  ```json
  {
    "detail": "Rate limit exceeded. Maximum 15 requests per minute per email. Please try again later."
  }
  ```
- **500 Internal Server Error:** Database or server error
  ```json
  {
    "detail": "Failed to check authentication: [error message]"
  }
  ```

---

## Frontend Implementation

### Step 1: Remove Password Hashing Logic

**❌ REMOVE:** All password hashing code (bcryptjs, hash functions, etc.)

**✅ KEEP:** Simple password collection from form

### Step 2: Update API Call

**Old Code (Remove This):**
```typescript
// ❌ OLD - Don't use this anymore
import bcrypt from 'bcryptjs';

async function hashPassword(password: string): Promise<string> {
  const salt = await bcrypt.genSalt(12);
  return await bcrypt.hash(password, salt);
}

const passwordHash = await hashPassword(password);
const response = await fetch(`${API_BASE_URL}/oracle-auth`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: email,
    password_hash: passwordHash  // ❌ OLD
  })
});
```

**New Code (Use This):**
```typescript
// ✅ NEW - Simple and secure
const response = await fetch(`${API_BASE_URL}/oracle-auth`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: email,
    password: password  // ✅ Plain password - HTTPS encrypts it
  })
});
```

---

## Complete Implementation Examples

### TypeScript/Next.js Example

#### 1. API Utility Function

Create: `lib/api/oracle-auth.ts`

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface OracleAuthRequest {
  email: string;
  password: string;  // Plain text password
}

export interface OracleAuthResponse {
  authenticated: boolean;
  is_admin: boolean;
}

export interface OracleAuthError {
  detail: string;
  status?: number;
}

/**
 * Authenticate user with email and plain password.
 * Password is transmitted over HTTPS and verified by backend using bcrypt.
 * 
 * @param email - User email address
 * @param password - Plain text password (will be encrypted by HTTPS)
 * @returns Promise with authenticated status and is_admin flag
 * @throws Error if rate limit exceeded or server error
 */
export async function authenticateUser(
  email: string,
  password: string
): Promise<OracleAuthResponse> {
  const response = await fetch(`${API_BASE_URL}/oracle-auth`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      password: password,  // Plain password - HTTPS handles encryption
    }),
  });

  // Handle rate limiting
  if (response.status === 429) {
    const errorData: OracleAuthError = await response.json();
    throw new Error(`Rate limit exceeded: ${errorData.detail}`);
  }

  // Handle server errors
  if (!response.ok) {
    const errorData: OracleAuthError = await response.json();
    throw new Error(`Authentication failed: ${errorData.detail || response.statusText}`);
  }

  const data: OracleAuthResponse = await response.json();
  return data;
}
```

#### 2. Login Component

Example: `app/login/page.tsx` (App Router) or `pages/login.tsx` (Pages Router)

```typescript
'use client'; // For App Router

import { useState } from 'react';
import { useRouter } from 'next/navigation'; // App Router
// import { useRouter } from 'next/router'; // Pages Router
import { authenticateUser } from '@/lib/api/oracle-auth';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Call authentication API with plain password
      const authResponse = await authenticateUser(email, password);
      
      // Handle response
      if (authResponse.authenticated) {
        // Authentication successful
        console.log('Authentication successful!', {
          email,
          isAdmin: authResponse.is_admin
        });
        
        // TODO: Store authentication state (session, token, etc.)
        // TODO: Store is_admin flag for role-based access control
        
        // Redirect to dashboard or home page
        router.push('/dashboard');
      } else {
        // Authentication failed
        setError('Invalid email or password');
      }
    } catch (err: any) {
      // Handle errors (rate limit, network, etc.)
      setError(err.message || 'Authentication failed. Please try again.');
      console.error('Authentication error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4 max-w-md">
      <h1 className="text-2xl font-bold mb-6">Login</h1>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium mb-1">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="user@example.com"
          />
        </div>
        
        <div>
          <label htmlFor="password" className="block text-sm font-medium mb-1">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            placeholder="Enter your password"
          />
        </div>
        
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
        
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Authenticating...' : 'Login'}
        </button>
      </form>
    </div>
  );
}
```

#### 3. JavaScript Version (No TypeScript)

Create: `lib/api/oracle-auth.js`

```javascript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

/**
 * Authenticate user with email and plain password.
 * @param {string} email - User email address
 * @param {string} password - Plain text password
 * @returns {Promise<{authenticated: boolean, is_admin: boolean}>}
 */
export async function authenticateUser(email, password) {
  const response = await fetch(`${API_BASE_URL}/oracle-auth`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      password: password,  // Plain password
    }),
  });

  if (response.status === 429) {
    const errorData = await response.json();
    throw new Error(`Rate limit exceeded: ${errorData.detail}`);
  }

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(`Authentication failed: ${errorData.detail || response.statusText}`);
  }

  return await response.json();
}
```

---

## Migration Steps

### Step 1: Remove Old Dependencies

**Remove bcryptjs (no longer needed):**
```bash
npm uninstall bcryptjs @types/bcryptjs
```

### Step 2: Update API Calls

**Find and replace all instances of:**
- `password_hash` → `password`
- Remove all `hashPassword()` calls
- Remove all `bcrypt` imports

### Step 3: Update Request Bodies

**Before:**
```typescript
body: JSON.stringify({
  email: email,
  password_hash: await hashPassword(password)
})
```

**After:**
```typescript
body: JSON.stringify({
  email: email,
  password: password  // Plain password
})
```

### Step 4: Remove Hash Storage Files

**Delete any files that stored password hashes:**
- `app/utils/user-hashes.ts` (if exists)
- `lib/user-hashes.ts` (if exists)
- Any other files with pre-stored password hashes

### Step 5: Test Authentication

Test with known credentials:
```typescript
// Test user
const email = 'dearp@openbankingsolutions.com';
const password = '@Buttermilk1985!!';

const result = await authenticateUser(email, password);
console.log(result); // { authenticated: true, is_admin: true }
```

---

## Security Considerations

### Why Plain Password Over HTTPS is Safe

**✅ Standard Practice:**
- HTTPS encrypts all data in transit (including passwords)
- This is how 99% of web applications handle authentication
- Backend uses bcrypt.verify() for secure password comparison
- Password is never logged or stored in plain text

**✅ Security Benefits:**
- No password hashes in frontend code (major security improvement)
- Standard authentication pattern (easier to audit and maintain)
- Timing-safe comparison via bcrypt
- Rate limiting prevents brute force attacks

**✅ What Happens:**
1. User enters password in form
2. Password sent over HTTPS (encrypted)
3. Backend receives password
4. Backend uses `bcrypt.verify(password, stored_hash)` to check
5. Password never stored or logged

### Important Notes

- **Always use HTTPS in production** - Never send passwords over HTTP
- **Never log passwords** - Even in development, don't console.log passwords
- **Rate limiting** - Backend limits to 15 requests/minute per email
- **Error messages** - Don't reveal if email exists (generic error messages)

---

## Testing

### Test Cases

#### 1. Valid Credentials
```typescript
const result = await authenticateUser(
  'dearp@openbankingsolutions.com',
  '@Buttermilk1985!!'
);
// Expected: { authenticated: true, is_admin: true }
```

#### 2. Invalid Password
```typescript
const result = await authenticateUser(
  'dearp@openbankingsolutions.com',
  'wrongpassword'
);
// Expected: { authenticated: false, is_admin: false }
```

#### 3. Non-existent User
```typescript
const result = await authenticateUser(
  'nonexistent@example.com',
  'anypassword'
);
// Expected: { authenticated: false, is_admin: false }
```

#### 4. Rate Limiting
```typescript
// Make 16 requests in quick succession
for (let i = 0; i < 16; i++) {
  try {
    await authenticateUser('test@example.com', 'password');
  } catch (err) {
    // 16th request should fail with rate limit error
    console.log(err.message); // "Rate limit exceeded: ..."
  }
}
```

### cURL Testing

```bash
# Valid credentials
curl -X POST "http://localhost:8001/oracle-auth" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dearp@openbankingsolutions.com",
    "password": "@Buttermilk1985!!"
  }'

# Expected response:
# {"authenticated": true, "is_admin": true}

# Invalid password
curl -X POST "http://localhost:8001/oracle-auth" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dearp@openbankingsolutions.com",
    "password": "wrongpassword"
  }'

# Expected response:
# {"authenticated": false, "is_admin": false}
```

---

## Environment Variables

### Required

```env
# API Base URL
NEXT_PUBLIC_API_URL=http://localhost:8001
```

**For production:**
```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

---

## Error Handling

### Rate Limit Error
```typescript
try {
  await authenticateUser(email, password);
} catch (error) {
  if (error.message.includes('Rate limit exceeded')) {
    // Show user-friendly message
    setError('Too many login attempts. Please wait a minute and try again.');
  }
}
```

### Network Error
```typescript
try {
  await authenticateUser(email, password);
} catch (error) {
  if (error.message.includes('fetch')) {
    setError('Network error. Please check your connection.');
  }
}
```

### Generic Error Handling
```typescript
try {
  const result = await authenticateUser(email, password);
  if (result.authenticated) {
    // Success
  } else {
    setError('Invalid email or password');
  }
} catch (error) {
  setError(error.message || 'Authentication failed. Please try again.');
}
```

---

## Session Management (Optional)

After successful authentication, you may want to store the session:

```typescript
// After successful authentication
if (authResponse.authenticated) {
  // Store in localStorage (simple approach)
  localStorage.setItem('authenticated', 'true');
  localStorage.setItem('email', email);
  localStorage.setItem('is_admin', authResponse.is_admin.toString());
  
  // Or use cookies, session storage, or a state management library
  // Or implement JWT tokens if backend supports it
}
```

---

## Summary

### What Changed
- ❌ **Removed:** Client-side password hashing (bcryptjs)
- ❌ **Removed:** `password_hash` field in API requests
- ✅ **Added:** Simple `password` field (plain text)
- ✅ **Simplified:** Frontend code is now much simpler

### Benefits
- 🔒 **More Secure:** No password hashes in frontend code
- 📚 **Standard Pattern:** Industry-standard authentication flow
- 🧹 **Cleaner Code:** Less complexity, easier to maintain
- ✅ **Better UX:** Faster authentication (no hashing delay)

### Implementation Checklist
- [ ] Remove `bcryptjs` dependency
- [ ] Update API call to use `password` instead of `password_hash`
- [ ] Remove all password hashing functions
- [ ] Remove any files with stored password hashes
- [ ] Update login form to send plain password
- [ ] Test authentication with valid credentials
- [ ] Test error handling (invalid password, rate limit, etc.)
- [ ] Verify HTTPS is used in production
- [ ] Update documentation

---

## Questions?

If you have questions about the implementation:
1. Check the backend API documentation: `PLAN_PASSWORD_AUTHENTICATION.md`
2. Test the endpoint directly with cURL
3. Check browser network tab for request/response details
4. Review backend logs for authentication attempts

---

**Last Updated:** 2026-01-05  
**Backend Version:** Task-000019 (Authentication Refactoring)  
**API Endpoint:** `POST /oracle-auth`

