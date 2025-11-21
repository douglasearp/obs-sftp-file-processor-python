# Next.js Frontend Plan: Oracle Auth Integration

## Overview

This plan provides instructions for integrating the `/oracle-auth` endpoint into your Next.js frontend application. The frontend needs to:
1. Collect email and password from the user
2. Hash the password using bcrypt to match the backend's PASSWORD_HASH format
3. Call the `/oracle-auth` API endpoint
4. Handle the response (authenticated: true/false and is_admin flag)

---

## Backend Endpoint Details

### Endpoint Information
- **URL:** `POST /oracle-auth`
- **Base URL:** `http://localhost:8002` (local) or your production API URL
- **Content-Type:** `application/json`

### Request Format
```json
{
  "email": "user@example.com",
  "password_hash": "$2b$12$HyRo2NsnVPk9raBPcYpGRODKMIn75e0AHV48/y8XP0fgRt8e1ZbCy"
}
```

### Response Format
```json
{
  "authenticated": true,  // true = match found, false = no match
  "is_admin": true        // true if user is admin (only set when authenticated=true)
}
```

### Error Responses
- **429 Too Many Requests:** Rate limit exceeded (15 requests/minute per email)
- **500 Internal Server Error:** Database or server error

---

## Password Hashing Requirements

### Backend Hash Format
- **Algorithm:** bcrypt
- **Rounds:** 12 (cost factor)
- **Format:** `$2b$12$...` (bcrypt with 12 rounds)
- **Example:** `$2b$12$HyRo2NsnVPk9raBPcYpGRODKMIn75e0AHV48/y8XP0fgRt8e1ZbCy`

### Important Notes
- The backend stores **pre-hashed passwords** in the database
- The frontend must hash the **plain password** to match the stored hash
- Use **bcryptjs** library (JavaScript version of bcrypt)
- Must use **12 rounds** to match backend configuration

---

## Implementation Steps

### Step 1: Install Required Dependencies

```bash
npm install bcryptjs
npm install --save-dev @types/bcryptjs  # If using TypeScript
```

**Alternative:** If you prefer async/await pattern:
```bash
npm install bcryptjs
```

---

### Step 2: Create Password Hashing Utility

Create a utility file: `lib/auth-utils.ts` (or `.js`)

```typescript
import bcrypt from 'bcryptjs';

/**
 * Hash a password using bcrypt with 12 rounds (matching backend)
 * @param password - Plain text password
 * @returns Hashed password string
 */
export async function hashPassword(password: string): Promise<string> {
  const saltRounds = 12; // Must match backend (12 rounds)
  const hashedPassword = await bcrypt.hash(password, saltRounds);
  return hashedPassword;
}

/**
 * Verify a password against a hash (optional, for client-side validation)
 * @param password - Plain text password
 * @param hash - Bcrypt hash to verify against
 * @returns True if password matches hash
 */
export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return await bcrypt.compare(password, hash);
}
```

**JavaScript Version:**
```javascript
const bcrypt = require('bcryptjs');

async function hashPassword(password) {
  const saltRounds = 12; // Must match backend
  const hashedPassword = await bcrypt.hash(password, saltRounds);
  return hashedPassword;
}

async function verifyPassword(password, hash) {
  return await bcrypt.compare(password, hash);
}

module.exports = { hashPassword, verifyPassword };
```

---

### Step 3: Create API Client Function

Create: `lib/api/oracle-auth.ts` (or `.js`)

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

export interface OracleAuthRequest {
  email: string;
  password_hash: string;
}

export interface OracleAuthResponse {
  authenticated: boolean; // true = match found, false = no match
  is_admin: boolean;      // true if user is admin (only meaningful when authenticated=true)
}

export interface OracleAuthError {
  detail: string;
  status: number;
}

/**
 * Call oracle-auth endpoint to verify email and password hash
 * @param email - User email address
 * @param passwordHash - Bcrypt hashed password
 * @returns Promise with authenticated status and is_admin flag
 */
export async function callOracleAuth(
  email: string,
  passwordHash: string
): Promise<OracleAuthResponse> {
  const response = await fetch(`${API_BASE_URL}/oracle-auth`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      password_hash: passwordHash,
    }),
  });

  // Handle rate limiting
  if (response.status === 429) {
    const errorData = await response.json();
    throw new Error(`Rate limit exceeded: ${errorData.detail}`);
  }

  // Handle server errors
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(`Authentication failed: ${errorData.detail || response.statusText}`);
  }

  const data: OracleAuthResponse = await response.json();
  return data;
}
```

**JavaScript Version:**
```javascript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

async function callOracleAuth(email, passwordHash) {
  const response = await fetch(`${API_BASE_URL}/oracle-auth`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      password_hash: passwordHash,
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

  const data = await response.json();
  return data;
}

module.exports = { callOracleAuth };
```

---

### Step 4: Create Login Component/Page

Example: `app/login/page.tsx` (App Router) or `pages/login.tsx` (Pages Router)

```typescript
'use client'; // For App Router

import { useState } from 'react';
import { hashPassword } from '@/lib/auth-utils';
import { callOracleAuth } from '@/lib/api/oracle-auth';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<OracleAuthResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      // Step 1: Hash the password
      const passwordHash = await hashPassword(password);
      
      // Step 2: Call oracle-auth endpoint
      const authResponse = await callOracleAuth(email, passwordHash);
      setResponse(authResponse);
      
      // Step 3: Handle response
      if (authResponse.authenticated) {
        // Authentication successful - redirect or set session
        console.log('Authentication successful!', {
          isAdmin: authResponse.is_admin
        });
        // TODO: Handle successful authentication (redirect, set token, etc.)
        // TODO: Store is_admin flag for role-based access control
      } else {
        // Authentication failed
        setError('Invalid email or password');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
      console.error('Authentication error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Login</h1>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block mb-2">
            Email:
          </label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-3 py-2 border rounded"
            disabled={loading}
          />
        </div>

        <div>
          <label htmlFor="password" className="block mb-2">
            Password:
          </label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full px-3 py-2 border rounded"
            disabled={loading}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-400"
        >
          {loading ? 'Authenticating...' : 'Login'}
        </button>
      </form>

      {error && (
        <div className="mt-4 p-3 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      {response && (
        <div className={`mt-4 p-3 rounded ${
          response.authenticated ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
        }`}>
          {response.authenticated ? (
            <div>
              ✅ Authentication successful!
              {response.is_admin && <div className="mt-2 text-sm font-semibold">🔑 Admin user</div>}
            </div>
          ) : (
            '❌ Authentication failed'
          )}
        </div>
      )}
    </div>
  );
}
```

**JavaScript Version:**
```javascript
import { useState } from 'react';
import { hashPassword } from '@/lib/auth-utils';
import { callOracleAuth } from '@/lib/api/oracle-auth';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      // Hash the password
      const passwordHash = await hashPassword(password);
      
      // Call oracle-auth endpoint
      const authResponse = await callOracleAuth(email, passwordHash);
      setResponse(authResponse);
      
      // Handle response
      if (authResponse.authenticated) {
        console.log('Authentication successful!', {
          isAdmin: authResponse.is_admin
        });
        // TODO: Handle successful authentication
        // TODO: Store is_admin flag for role-based access control
      } else {
        setError('Invalid email or password');
      }
    } catch (err) {
      setError(err.message || 'Authentication failed');
      console.error('Authentication error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Login</h1>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block mb-2">Email:</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-3 py-2 border rounded"
            disabled={loading}
          />
        </div>

        <div>
          <label htmlFor="password" className="block mb-2">Password:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full px-3 py-2 border rounded"
            disabled={loading}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-400"
        >
          {loading ? 'Authenticating...' : 'Login'}
        </button>
      </form>

      {error && (
        <div className="mt-4 p-3 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      {response && (
        <div className={`mt-4 p-3 rounded ${
          response.authenticated ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
        }`}>
          {response.authenticated ? (
            <div>
              ✅ Authentication successful!
              {response.is_admin && <div className="mt-2 text-sm font-semibold">🔑 Admin user</div>}
            </div>
          ) : (
            '❌ Authentication failed'
          )}
        </div>
      )}
    </div>
  );
}
```

---

## Environment Variables

Create `.env.local` in your Next.js project:

```env
NEXT_PUBLIC_API_URL=http://localhost:8002
```

For production:
```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

---

## Important Implementation Notes

### 1. Password Hashing Must Match Backend

- **Rounds:** Must be **12** (not 10, not 14)
- **Library:** Use `bcryptjs` (not `bcrypt` - that's for Node.js server-side only)
- **Format:** Result will be `$2b$12$...` format

### 2. Rate Limiting Awareness

- **Limit:** 15 requests per minute per email
- **Handle 429:** Show user-friendly message
- **UI Feedback:** Consider showing remaining attempts or cooldown timer

### 3. Security Considerations

- **Client-Side Hashing:** Password is hashed on client before sending
- **HTTPS Required:** Always use HTTPS in production
- **No Plain Password:** Never send plain password to API
- **Error Messages:** Don't reveal if email exists (generic error messages)

### 4. Response Handling

- **authenticated = true:** Email and password hash match → Authentication successful
  - **is_admin = true:** User has admin privileges
  - **is_admin = false:** Regular user
- **authenticated = false:** No match found → Authentication failed
  - **is_admin** will be false (not meaningful when not authenticated)
- **429 Error:** Rate limit exceeded → Show cooldown message
- **500 Error:** Server error → Show generic error

---

## Complete Flow Diagram

```
User Input
    ↓
[Email + Password]
    ↓
Hash Password (bcrypt, 12 rounds)
    ↓
[Email + Password Hash]
    ↓
POST /oracle-auth
    ↓
Backend checks API_USERS table
    ↓
Response: { result: 1 or 0 }
    ↓
Handle Response
    ├─ result = 1 → Success (redirect/set session)
    └─ result = 0 → Show error
```

---

## Testing

### Test with Valid Credentials

```typescript
// Test user from Task-000006
const email = 'dearp@openbankingsolutions.com';
const password = '@Buttermilk1985!!';

// Hash password
const passwordHash = await hashPassword(password);
// Result: $2b$12$HyRo2NsnVPk9raBPcYpGRODKMIn75e0AHV48/y8XP0fgRt8e1ZbCy

// Call API
const response = await callOracleAuth(email, passwordHash);
// Expected: { authenticated: true, is_admin: true }
```

### Test with Invalid Credentials

```typescript
const email = 'dearp@openbankingsolutions.com';
const password = 'wrongpassword';

const passwordHash = await hashPassword(password);
const response = await callOracleAuth(email, passwordHash);
// Expected: { authenticated: false, is_admin: false }
```

---

## Error Handling Examples

### Rate Limit Error

```typescript
try {
  const response = await callOracleAuth(email, passwordHash);
} catch (error) {
  if (error.message.includes('Rate limit exceeded')) {
    // Show: "Too many attempts. Please wait 1 minute before trying again."
    setError('Too many login attempts. Please wait a moment.');
  }
}
```

### Network Error

```typescript
try {
  const response = await callOracleAuth(email, passwordHash);
} catch (error) {
  if (error.message.includes('fetch')) {
    // Network error
    setError('Unable to connect to server. Please check your connection.');
  }
}
```

---

## TypeScript Types (Optional)

If using TypeScript, create: `types/oracle-auth.ts`

```typescript
export interface OracleAuthRequest {
  email: string;
  password_hash: string;
}

export interface OracleAuthResponse {
  authenticated: boolean; // true = match found, false = no match
  is_admin: boolean;      // true if user is admin (only meaningful when authenticated=true)
}

export interface OracleAuthError {
  detail: string;
  status?: number;
}
```

---

## Summary Checklist

- [ ] Install `bcryptjs` package
- [ ] Create password hashing utility (`hashPassword` function)
- [ ] Create API client function (`callOracleAuth`)
- [ ] Create login form component
- [ ] Add environment variable for API URL
- [ ] Handle rate limiting (429 errors)
- [ ] Handle authentication success (authenticated = true)
- [ ] Handle authentication failure (authenticated = false)
- [ ] Handle is_admin flag for role-based access control
- [ ] Add loading states
- [ ] Add error messages
- [ ] Test with valid credentials
- [ ] Test with invalid credentials
- [ ] Test rate limiting

---

## Quick Reference

### Password Hash Format
- **Algorithm:** bcrypt
- **Rounds:** 12
- **Format:** `$2b$12$[salt][hash]`
- **Length:** ~60 characters

### API Endpoint
- **Method:** POST
- **URL:** `/oracle-auth`
- **Request:** `{ email: string, password_hash: string }`
- **Response:** 
  ```json
  {
    "authenticated": true,  // true = match found, false = no match
    "is_admin": true        // true if user is admin (only when authenticated=true)
  }
  ```

### Rate Limiting
- **Limit:** 15 requests per minute per email
- **Error Code:** 429
- **Error Message:** "Rate limit exceeded. Maximum 15 requests per minute per email."

### Response Fields
- **authenticated:** `true` if email and password hash match, `false` otherwise
- **is_admin:** `true` if user has admin privileges (only meaningful when `authenticated=true`)
  - Use this flag for role-based access control in your frontend
  - Admin users can access admin-only features
  - Regular users have limited access

---

## Example Complete Implementation

See the code examples above for:
1. Password hashing utility
2. API client function
3. Complete login component

All code is ready to use in your Next.js application!

