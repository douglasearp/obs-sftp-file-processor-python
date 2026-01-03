"""Oracle database models for ACH_ACCOUNT_NUMBER_SWAPS table."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AchAccountSwapBase(BaseModel):
    """Base model for ACH_ACCOUNT_NUMBER_SWAPS table."""
    
    original_dfi_account_number: Optional[str] = Field(None, max_length=17, description="Original DFI account number")
    swap_account_number: Optional[str] = Field(None, max_length=17, description="Swapped/replacement account number")
    swap_memo: str = Field(..., max_length=255, description="Memo/description for the swap")
    created_by_user: str = Field(..., max_length=50, description="User who created the record")
    updated_by_user: Optional[str] = Field(None, max_length=50, description="User who last updated the record")


class AchAccountSwapCreate(AchAccountSwapBase):
    """Model for creating ACH_ACCOUNT_NUMBER_SWAPS records."""
    pass


class AchAccountSwapUpdate(BaseModel):
    """Model for updating ACH_ACCOUNT_NUMBER_SWAPS records."""
    
    original_dfi_account_number: Optional[str] = Field(None, max_length=17, description="Original DFI account number")
    swap_account_number: Optional[str] = Field(None, max_length=17, description="Swapped/replacement account number")
    swap_memo: Optional[str] = Field(None, max_length=255, description="Memo/description for the swap")
    updated_by_user: Optional[str] = Field(None, max_length=50, description="User who updated the record")


class AchAccountSwap(AchAccountSwapBase):
    """Complete ACH_ACCOUNT_NUMBER_SWAPS model with all fields."""
    
    swap_id: int = Field(..., description="Primary key - auto-generated")
    created_date: datetime = Field(..., description="Creation timestamp")
    updated_date: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class AchAccountSwapResponse(BaseModel):
    """Response model for ACH_ACCOUNT_NUMBER_SWAPS API."""
    
    swap_id: int
    original_dfi_account_number: Optional[str] = None
    swap_account_number: Optional[str] = None
    swap_memo: str
    created_by_user: str
    created_date: datetime
    updated_by_user: Optional[str] = None
    updated_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AchAccountSwapListResponse(BaseModel):
    """Response model for ACH_ACCOUNT_NUMBER_SWAPS list."""
    
    swaps: list[AchAccountSwapResponse]
    total_count: int


class SwapLookupResponse(BaseModel):
    """Response model for swap lookup by ORIGINAL_DFI_ACCOUNT_NUMBER."""
    
    swap_account_number: Optional[str] = None
    swap_memo: str
    swap_id: int
    original_dfi_account_number: Optional[str] = None

