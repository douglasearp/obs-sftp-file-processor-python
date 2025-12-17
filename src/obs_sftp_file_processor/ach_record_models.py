"""Oracle database models for ACH record type tables."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# File Header Record (Type Code: 1)
class AchFileHeaderBase(BaseModel):
    """Base model for ACH_FILE_HEADER table."""
    
    file_id: int = Field(..., description="Foreign key to ACH_FILES")
    record_type_code: str = Field("1", description="Record type code")
    priority_code: Optional[str] = Field(None, description="Priority code")
    immediate_destination: Optional[str] = Field(None, description="Immediate destination")
    immediate_origin: Optional[str] = Field(None, description="Immediate origin")
    file_creation_date: Optional[str] = Field(None, description="File creation date")
    file_creation_time: Optional[str] = Field(None, description="File creation time")
    file_id_modifier: Optional[str] = Field(None, description="File ID modifier")
    record_size: Optional[str] = Field("094", description="Record size")
    blocking_factor: Optional[str] = Field("10", description="Blocking factor")
    format_code: Optional[str] = Field("1", description="Format code")
    immediate_dest_name: Optional[str] = Field(None, description="Immediate destination name")
    immediate_origin_name: Optional[str] = Field(None, description="Immediate origin name")
    reference_code: Optional[str] = Field(None, description="Reference code")
    raw_record: Optional[str] = Field(None, description="Raw 94-character record")


class AchFileHeaderCreate(AchFileHeaderBase):
    """Model for creating ACH_FILE_HEADER records."""
    pass


class AchFileHeader(AchFileHeaderBase):
    """Complete ACH_FILE_HEADER model."""
    
    file_header_id: int = Field(..., description="Primary key")
    created_date: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


# Batch Header Record (Type Code: 5)
class AchBatchHeaderBase(BaseModel):
    """Base model for ACH_BATCH_HEADER table."""
    
    file_id: int = Field(..., description="Foreign key to ACH_FILES")
    batch_number: int = Field(..., description="Batch number")
    record_type_code: str = Field("5", description="Record type code")
    service_class_code: Optional[str] = Field(None, description="Service class code")
    company_name: Optional[str] = Field(None, description="Company name")
    company_discretionary_data: Optional[str] = Field(None, description="Company discretionary data")
    company_identification: Optional[str] = Field(None, description="Company identification")
    standard_entry_class_code: Optional[str] = Field(None, description="Standard entry class code")
    company_entry_description: Optional[str] = Field(None, description="Company entry description")
    company_descriptive_date: Optional[str] = Field(None, description="Company descriptive date")
    effective_entry_date: Optional[str] = Field(None, description="Effective entry date")
    settlement_date: Optional[str] = Field(None, description="Settlement date")
    originator_status_code: Optional[str] = Field(None, description="Originator status code")
    originating_dfi_id: Optional[str] = Field(None, description="Originating DFI ID")
    raw_record: Optional[str] = Field(None, description="Raw 94-character record")


class AchBatchHeaderCreate(AchBatchHeaderBase):
    """Model for creating ACH_BATCH_HEADER records."""
    pass


class AchBatchHeader(AchBatchHeaderBase):
    """Complete ACH_BATCH_HEADER model."""
    
    batch_header_id: int = Field(..., description="Primary key")
    created_date: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


# Entry Detail Record (Type Code: 6)
class AchEntryDetailBase(BaseModel):
    """Base model for ACH_ENTRY_DETAIL table."""
    
    file_id: int = Field(..., description="Foreign key to ACH_FILES")
    batch_number: int = Field(..., description="Batch number")
    record_type_code: str = Field("6", description="Record type code")
    transaction_code: Optional[str] = Field(None, description="Transaction code")
    receiving_dfi_id: Optional[str] = Field(None, description="Receiving DFI ID")
    check_digit: Optional[str] = Field(None, description="Check digit")
    dfi_account_number: Optional[str] = Field(None, description="DFI account number")
    amount: int = Field(0, description="Amount in cents")
    amount_decimal: Optional[float] = Field(None, description="Amount as decimal")
    individual_id_number: Optional[str] = Field(None, description="Individual ID number")
    individual_name: Optional[str] = Field(None, description="Individual name")
    discretionary_data: Optional[str] = Field(None, description="Discretionary data")
    addenda_record_indicator: Optional[str] = Field("0", description="Addenda record indicator")
    trace_number: Optional[str] = Field(None, description="Trace number")
    trace_sequence_number: Optional[int] = Field(None, description="Trace sequence number")
    raw_record: Optional[str] = Field(None, description="Raw 94-character record")


class AchEntryDetailCreate(AchEntryDetailBase):
    """Model for creating ACH_ENTRY_DETAIL records."""
    pass


class AchEntryDetail(AchEntryDetailBase):
    """Complete ACH_ENTRY_DETAIL model."""
    
    entry_detail_id: int = Field(..., description="Primary key")
    created_date: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


# Addenda Record (Type Code: 7)
class AchAddendaBase(BaseModel):
    """Base model for ACH_ADDENDA table."""
    
    file_id: int = Field(..., description="Foreign key to ACH_FILES")
    entry_detail_id: Optional[int] = Field(None, description="Foreign key to ACH_ENTRY_DETAIL")
    batch_number: int = Field(..., description="Batch number")
    record_type_code: str = Field("7", description="Record type code")
    addenda_type_code: Optional[str] = Field(None, description="Addenda type code")
    payment_related_info: Optional[str] = Field(None, description="Payment related information")
    addenda_sequence_number: Optional[int] = Field(None, description="Addenda sequence number")
    entry_detail_sequence_num: Optional[int] = Field(None, description="Entry detail sequence number")
    raw_record: Optional[str] = Field(None, description="Raw 94-character record")


class AchAddendaCreate(AchAddendaBase):
    """Model for creating ACH_ADDENDA records."""
    pass


class AchAddenda(AchAddendaBase):
    """Complete ACH_ADDENDA model."""
    
    addenda_id: int = Field(..., description="Primary key")
    created_date: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


# Batch Control Record (Type Code: 8)
class AchBatchControlBase(BaseModel):
    """Base model for ACH_BATCH_CONTROL table."""
    
    file_id: int = Field(..., description="Foreign key to ACH_FILES")
    batch_number: int = Field(..., description="Batch number")
    record_type_code: str = Field("8", description="Record type code")
    service_class_code: Optional[str] = Field(None, description="Service class code")
    entry_addenda_count: Optional[int] = Field(None, description="Entry addenda count")
    entry_hash: Optional[str] = Field(None, description="Entry hash")
    total_debit_amount: int = Field(0, description="Total debit amount in cents")
    total_debit_amount_decimal: Optional[float] = Field(None, description="Total debit amount as decimal")
    total_credit_amount: int = Field(0, description="Total credit amount in cents")
    total_credit_amount_decimal: Optional[float] = Field(None, description="Total credit amount as decimal")
    company_identification: Optional[str] = Field(None, description="Company identification")
    message_auth_code: Optional[str] = Field(None, description="Message authentication code")
    reserved: Optional[str] = Field(None, description="Reserved field")
    originating_dfi_id: Optional[str] = Field(None, description="Originating DFI ID")
    raw_record: Optional[str] = Field(None, description="Raw 94-character record")


class AchBatchControlCreate(AchBatchControlBase):
    """Model for creating ACH_BATCH_CONTROL records."""
    pass


class AchBatchControl(AchBatchControlBase):
    """Complete ACH_BATCH_CONTROL model."""
    
    batch_control_id: int = Field(..., description="Primary key")
    created_date: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


# File Control Record (Type Code: 9)
class AchFileControlBase(BaseModel):
    """Base model for ACH_FILE_CONTROL table."""
    
    file_id: int = Field(..., description="Foreign key to ACH_FILES")
    record_type_code: str = Field("9", description="Record type code")
    batch_count: Optional[int] = Field(None, description="Batch count")
    block_count: Optional[int] = Field(None, description="Block count")
    entry_addenda_count: Optional[int] = Field(None, description="Entry addenda count")
    entry_hash: Optional[str] = Field(None, description="Entry hash")
    total_debit_amount: int = Field(0, description="Total debit amount in cents")
    total_debit_amount_decimal: Optional[float] = Field(None, description="Total debit amount as decimal")
    total_credit_amount: int = Field(0, description="Total credit amount in cents")
    total_credit_amount_decimal: Optional[float] = Field(None, description="Total credit amount as decimal")
    reserved: Optional[str] = Field(None, description="Reserved field")
    raw_record: Optional[str] = Field(None, description="Raw 94-character record")


class AchFileControlCreate(AchFileControlBase):
    """Model for creating ACH_FILE_CONTROL records."""
    pass


class AchFileControl(AchFileControlBase):
    """Complete ACH_FILE_CONTROL model."""
    
    file_control_id: int = Field(..., description="Primary key")
    created_date: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True

