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
    client_id: str = Field(..., description="Client ID to use in filename pattern")


class AddSftpAchFileResponse(BaseModel):
    """Response model for adding ACH file to SFTP server."""
    
    success: bool = Field(..., description="Whether the upload was successful")
    filename: str = Field(..., description="Generated filename")
    remote_path: str = Field(..., description="Remote path where file was uploaded")
    file_size: int = Field(..., description="Size of uploaded file in bytes")
    message: str = Field(..., description="Success or error message")
