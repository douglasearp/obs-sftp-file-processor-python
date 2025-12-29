"""Oracle database models for FI_HOLIDAYS table."""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field


class FiHolidayBase(BaseModel):
    """Base model for FI_HOLIDAYS table."""
    
    holiday_date: date = Field(..., description="Holiday date")
    holiday_name: str = Field(..., description="Holiday name/description")
    is_active: Optional[int] = Field(1, description="Active status (1=active, 0=inactive)")
    created_by_user: Optional[str] = Field(None, description="User who created the record")
    updated_by_user: Optional[str] = Field(None, description="User who last updated the record")


class FiHolidayCreate(FiHolidayBase):
    """Model for creating FI_HOLIDAYS records."""
    pass


class FiHolidayUpdate(BaseModel):
    """Model for updating FI_HOLIDAYS records."""
    
    holiday_date: Optional[date] = Field(None, description="Holiday date")
    holiday_name: Optional[str] = Field(None, description="Holiday name/description")
    is_active: Optional[int] = Field(None, description="Active status (1=active, 0=inactive)")
    updated_by_user: Optional[str] = Field(None, description="User who updated the record")


class FiHoliday(FiHolidayBase):
    """Complete FI_HOLIDAYS model with all fields."""
    
    holiday_id: int = Field(..., description="Primary key - auto-generated")
    created_date: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_date: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class FiHolidayResponse(BaseModel):
    """Response model for FI_HOLIDAYS API."""
    
    holiday_id: int
    holiday_date: date
    holiday_name: str
    is_active: Optional[int] = None
    created_by_user: Optional[str] = None
    created_date: Optional[datetime] = None
    updated_by_user: Optional[str] = None
    updated_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FiHolidayListResponse(BaseModel):
    """Response model for FI_HOLIDAYS list."""
    
    holidays: list[FiHolidayResponse]
    total_count: int

