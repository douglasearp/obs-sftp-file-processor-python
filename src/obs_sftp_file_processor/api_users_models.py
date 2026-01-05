"""Oracle database models for API_USERS table."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ApiUserBase(BaseModel):
    """Base model for API_USERS table."""
    
    username: str = Field(..., max_length=50, description="Unique username for login")
    email: Optional[str] = Field(None, max_length=100, description="User email address")
    full_name: Optional[str] = Field(None, max_length=100, description="User full name")
    is_active: int = Field(1, description="Account active status (1=active, 0=inactive)")
    is_admin: int = Field(0, description="Admin flag (1=admin, 0=user)")


class ApiUserCreate(ApiUserBase):
    """Model for creating API_USERS records."""
    
    password: str = Field(..., description="Plain text password (will be hashed with bcrypt)")


class ApiUserUpdate(BaseModel):
    """Model for updating API_USERS records."""
    
    username: Optional[str] = Field(None, max_length=50, description="Unique username for login")
    email: Optional[str] = Field(None, max_length=100, description="User email address")
    full_name: Optional[str] = Field(None, max_length=100, description="User full name")
    password: Optional[str] = Field(None, description="Plain text password (will be hashed with bcrypt if provided)")
    is_active: Optional[int] = Field(None, description="Account active status (1=active, 0=inactive)")
    is_admin: Optional[int] = Field(None, description="Admin flag (1=admin, 0=user)")


class ApiUser(ApiUserBase):
    """Complete API_USERS model with all fields."""
    
    user_id: int = Field(..., description="Primary key - auto-generated")
    created_date: datetime = Field(..., description="Creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last successful login timestamp")
    failed_login_attempts: int = Field(0, description="Counter for failed login attempts")
    locked_until: Optional[datetime] = Field(None, description="Account lock expiration timestamp")
    
    class Config:
        from_attributes = True


class ApiUserResponse(BaseModel):
    """Response model for API_USERS API."""
    
    user_id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: int
    is_admin: int
    created_date: datetime
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ApiUserListResponse(BaseModel):
    """Response model for API_USERS list."""
    
    users: list[ApiUserResponse]
    total_count: int

