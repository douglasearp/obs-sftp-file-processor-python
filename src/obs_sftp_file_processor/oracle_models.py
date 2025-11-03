"""Oracle database models for ACH_FILES table."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AchFileBase(BaseModel):
    """Base model for ACH_FILES table."""
    
    original_filename: str = Field(..., description="Original filename from SFTP")
    processing_status: str = Field("Pending", description="Processing status")
    file_contents: Optional[str] = Field(None, description="File contents as CLOB")
    created_by_user: str = Field("UnityBankUserName@UB.com", description="User who created the record")
    updated_by_user: Optional[str] = Field(None, description="User who last updated the record")


class AchFileCreate(AchFileBase):
    """Model for creating ACH_FILES records."""
    pass


class AchFileUpdate(BaseModel):
    """Model for updating ACH_FILES records."""
    
    processing_status: Optional[str] = Field(None, description="Processing status")
    file_contents: Optional[str] = Field(None, description="File contents as CLOB")
    updated_by_user: Optional[str] = Field(None, description="User who updated the record")


class AchFile(AchFileBase):
    """Complete ACH_FILES model with all fields."""
    
    file_id: int = Field(..., description="Primary key - auto-generated")
    created_date: datetime = Field(..., description="Creation timestamp")
    updated_date: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class AchFileResponse(BaseModel):
    """Response model for ACH_FILES API."""
    
    file_id: int
    original_filename: str
    processing_status: str
    file_contents: Optional[str] = None
    created_by_user: str
    created_date: datetime
    updated_by_user: Optional[str] = None
    updated_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AchFileListResponse(BaseModel):
    """Response model for ACH_FILES list."""
    
    files: list[AchFileResponse]
    total_count: int


class AchFileUpdateByFileIdRequest(BaseModel):
    """Model for updating ACH_FILES by file_id."""
    
    file_contents: str = Field(..., description="File contents to update")
    updated_by_user: str = Field("system-user", description="User who updated the record")
    updated_date: Optional[datetime] = Field(None, description="Update timestamp (defaults to CURRENT_TIMESTAMP if not provided)")
