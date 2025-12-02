"""Pydantic models for API requests and responses."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """File information model."""
    
    name: str = Field(..., description="File name")
    path: str = Field(..., description="File path")
    size: int = Field(..., description="File size in bytes")
    modified: float = Field(..., description="Last modified timestamp")
    is_directory: bool = Field(..., description="Whether the item is a directory")
    permissions: str = Field(..., description="File permissions")


class FileContent(BaseModel):
    """File content response model."""
    
    file_info: FileInfo = Field(..., description="File information")
    content: str = Field(..., description="File content as string")
    encoding: str = Field("utf-8", description="File encoding")
    content_type: str = Field(..., description="Detected content type")


class FileListResponse(BaseModel):
    """File list response model."""
    
    path: str = Field(..., description="Directory path")
    files: List[FileInfo] = Field(..., description="List of files and directories")
    total_count: int = Field(..., description="Total number of items")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")


class AddSftpAchFileRequest(BaseModel):
    """Request model for adding ACH file to SFTP server."""
    
    file_contents: str = Field(..., description="File contents to upload")
    filename: str = Field(..., description="Filename to use for the uploaded file")


class AddSftpAchFileResponse(BaseModel):
    """Response model for adding ACH file to SFTP server."""
    
    success: bool = Field(..., description="Whether the upload was successful")
    filename: str = Field(..., description="Generated filename")
    remote_path: str = Field(..., description="Remote path where file was uploaded")
    file_size: int = Field(..., description="Size of uploaded file in bytes")
    message: str = Field(..., description="Success or error message")


class ProcessSftpFileRequest(BaseModel):
    """Request model for processing SFTP file."""
    
    file_name: str = Field(..., description="Name of the file to process from upload folder")
    client_id: str = Field(..., description="Client ID to add to filename")
    created_by_user: Optional[str] = Field(None, description="User who created the record (optional)")


class ProcessSftpFileData(BaseModel):
    """Data model for successful file processing response."""
    
    file_id: int = Field(..., description="ACH_FILES record ID")
    file_blob_id: int = Field(..., description="ACH_FILES_BLOBS record ID")
    original_filename: str = Field(..., description="Original filename")
    renamed_filename: str = Field(..., description="Filename with client_id prefix")
    processing_status: str = Field(..., description="Processing status")
    archived_path: str = Field(..., description="Path to archived file")


class ProcessSftpFileErrorDetails(BaseModel):
    """Error details for file processing response."""
    
    file_id: Optional[int] = Field(None, description="ACH_FILES record ID if created")
    file_blob_id: Optional[int] = Field(None, description="ACH_FILES_BLOBS record ID if created")
    processing_status: str = Field(..., description="Processing status")
    stage: str = Field(..., description="Stage where error occurred")


class ProcessSftpFileResponse(BaseModel):
    """Response model for processing SFTP file."""
    
    success: bool = Field(..., description="Whether processing was successful")
    message: str = Field(..., description="Success or error message")
    data: Optional[ProcessSftpFileData] = Field(None, description="Success data")
    error: Optional[str] = Field(None, description="Error message if failed")
    details: Optional[ProcessSftpFileErrorDetails] = Field(None, description="Error details if failed")


class ArchivedFileInfo(BaseModel):
    """Information about an archived file."""
    
    name: str = Field(..., description="File name")
    size: int = Field(..., description="File size in bytes")
    created_date: Optional[datetime] = Field(None, description="File creation date")
    modified_date: datetime = Field(..., description="File modification date")


class ArchivedFileListResponse(BaseModel):
    """Response model for listing archived files."""
    
    files: List[ArchivedFileInfo] = Field(..., description="List of archived files")
    total: int = Field(..., description="Total number of files")
    limit: int = Field(..., description="Limit applied")
    offset: int = Field(..., description="Offset applied")


class ArchivedFileContentResponse(BaseModel):
    """Response model for archived file content."""
    
    file_name: str = Field(..., description="File name")
    content: str = Field(..., description="File content as string")
    size: int = Field(..., description="File size in bytes")


class OracleAuthRequest(BaseModel):
    """Request model for Oracle authentication check."""
    
    email: str = Field(..., description="User email address")
    password_hash: str = Field(..., description="Password hash to verify")


class OracleAuthResponse(BaseModel):
    """Response model for Oracle authentication check."""
    
    authenticated: bool = Field(..., description="True if email and password hash match, False otherwise")
    is_admin: bool = Field(False, description="True if user is admin, False otherwise (only set when authenticated=True)")
