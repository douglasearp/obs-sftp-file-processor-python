"""Oracle database models for ACH_FILES_BLOBS table."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AchFileBlobBase(BaseModel):
    """Base model for ACH_FILES_BLOBS table."""
    
    file_id: int = Field(..., description="Foreign key to ACH_FILES.FILE_ID")
    original_filename: str = Field(..., description="Original filename from SFTP")
    processing_status: str = Field("Pending", description="Processing status")
    file_contents: Optional[str] = Field(None, description="File contents as CLOB")
    created_by_user: str = Field("UnityBankUserName@UB.com", description="User who created the record")
    updated_by_user: Optional[str] = Field(None, description="User who last updated the record")


class AchFileBlobCreate(AchFileBlobBase):
    """Model for creating ACH_FILES_BLOBS records."""
    pass


class AchFileBlobUpdate(BaseModel):
    """Model for updating ACH_FILES_BLOBS records."""
    
    processing_status: Optional[str] = Field(None, description="Processing status")
    file_contents: Optional[str] = Field(None, description="File contents as CLOB")
    updated_by_user: Optional[str] = Field(None, description="User who updated the record")


class AchFileBlob(AchFileBlobBase):
    """Complete ACH_FILES_BLOBS model with all fields."""
    
    file_blob_id: int = Field(..., description="Primary key - auto-generated")
    created_date: datetime = Field(..., description="Creation timestamp")
    updated_date: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class AchFileBlobResponse(BaseModel):
    """Response model for ACH_FILES_BLOBS API."""
    
    file_blob_id: int
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

