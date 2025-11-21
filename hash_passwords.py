#!/usr/bin/env python3
"""Script to hash passwords for API_USERS table insertion."""

import sys
from passlib.context import CryptContext

# Create password context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hash_passwords.py <password>")
        sys.exit(1)
    
    password = sys.argv[1]
    hashed = hash_password(password)
    print(f"Password: {password}")
    print(f"Hashed:   {hashed}")
    print(f"\nUse this hash in SQL INSERT statement:")

