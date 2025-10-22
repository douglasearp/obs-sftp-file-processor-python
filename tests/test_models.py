"""Tests for Pydantic models."""

import pytest
from datetime import datetime
from src.obs_sftp_file_processor.models import (
    FileInfo,
    FileContent,
    FileListResponse,
    ErrorResponse,
    HealthResponse
)


def test_file_info():
    """Test FileInfo model."""
    file_info = FileInfo(
        name="test.txt",
        path="/data/test.txt",
        size=1024,
        modified=1640995200.0,
        is_directory=False,
        permissions="-rw-r--r--"
    )
    assert file_info.name == "test.txt"
    assert file_info.path == "/data/test.txt"
    assert file_info.size == 1024
    assert file_info.is_directory is False


def test_file_content():
    """Test FileContent model."""
    file_info = FileInfo(
        name="test.txt",
        path="/data/test.txt",
        size=1024,
        modified=1640995200.0,
        is_directory=False,
        permissions="-rw-r--r--"
    )
    
    content = FileContent(
        file_info=file_info,
        content="Hello, World!",
        encoding="utf-8",
        content_type="text/plain"
    )
    
    assert content.content == "Hello, World!"
    assert content.encoding == "utf-8"
    assert content.content_type == "text/plain"
    assert content.file_info.name == "test.txt"


def test_file_list_response():
    """Test FileListResponse model."""
    files = [
        FileInfo(
            name="file1.txt",
            path="/data/file1.txt",
            size=1024,
            modified=1640995200.0,
            is_directory=False,
            permissions="-rw-r--r--"
        )
    ]
    
    response = FileListResponse(
        path="/data",
        files=files,
        total_count=1
    )
    
    assert response.path == "/data"
    assert len(response.files) == 1
    assert response.total_count == 1


def test_error_response():
    """Test ErrorResponse model."""
    error = ErrorResponse(
        error="Test error",
        detail="Test detail"
    )
    
    assert error.error == "Test error"
    assert error.detail == "Test detail"
    assert isinstance(error.timestamp, datetime)


def test_health_response():
    """Test HealthResponse model."""
    health = HealthResponse(
        status="healthy",
        version="1.0.0"
    )
    
    assert health.status == "healthy"
    assert health.version == "1.0.0"
    assert isinstance(health.timestamp, datetime)
