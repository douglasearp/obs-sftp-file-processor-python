"""Oracle database models for ACH_FILE_LINES table."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AchFileLineBase(BaseModel):
    """Base model for ACH_FILE_LINES table."""
    
    file_id: int = Field(..., description="Foreign key to ACH_FILES table")
    line_number: int = Field(..., description="Sequential line number in the file")
    line_content: str = Field(..., description="Content of the line")
    line_errors: Optional[str] = Field(None, description="Validation errors for the line")
    created_by_user: str = Field("UnityBankUserName@UB.com", description="User who created the record")
    updated_by_user: Optional[str] = Field(None, description="User who last updated the record")


class AchFileLineCreate(AchFileLineBase):
    """Model for creating ACH_FILE_LINES records."""
    pass


class AchFileLineUpdate(BaseModel):
    """Model for updating ACH_FILE_LINES records."""
    
    line_content: Optional[str] = Field(None, description="Content of the line")
    line_errors: Optional[str] = Field(None, description="Validation errors for the line")
    updated_by_user: Optional[str] = Field(None, description="User who updated the record")


class AchFileLine(AchFileLineBase):
    """Complete ACH_FILE_LINES model with all fields."""
    
    file_lines_id: int = Field(..., description="Primary key - auto-generated")
    created_date: datetime = Field(..., description="Creation timestamp")
    updated_date: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class AchFileLineResponse(BaseModel):
    """Response model for ACH_FILE_LINES API."""
    
    file_lines_id: int
    file_id: int
    line_number: int
    line_content: str
    line_errors: Optional[str] = None
    created_by_user: str
    created_date: datetime
    updated_by_user: Optional[str] = None
    updated_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AchFileLineListResponse(BaseModel):
    """Response model for ACH_FILE_LINES list."""
    
    lines: list[AchFileLineResponse]
    total_count: int
