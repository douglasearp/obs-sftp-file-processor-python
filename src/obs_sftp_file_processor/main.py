"""Main FastAPI application."""

import mimetypes
from typing import List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from loguru import logger

from .config import config
from .models import FileContent, FileListResponse, HealthResponse, ErrorResponse, FileInfo
from .sftp_service import SFTPService


# Configure logging
logger.remove()
logger.add(
    "logs/app.log",
    rotation="1 day",
    retention="7 days",
    level=config.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
)
logger.add(
    lambda msg: print(msg, end=""),
    level=config.log_level,
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)

# Create FastAPI app
app = FastAPI(
    title=config.title,
    version=config.version,
    description="FastAPI application for reading files from Azure Storage SFTP server",
    debug=config.debug
)


def get_sftp_service() -> SFTPService:
    """Dependency to get SFTP service instance."""
    return SFTPService(config.sftp)


@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=config.version
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=config.version
    )


@app.get("/files", response_model=FileListResponse)
async def list_files(
    path: str = ".",
    sftp_service: SFTPService = Depends(get_sftp_service)
):
    """List files in the specified remote directory."""
    try:
        with sftp_service:
            files_data = sftp_service.list_files(path)
            files = [
                FileInfo(
                    name=file_data['name'],
                    path=f"{path}/{file_data['name']}".replace("//", "/"),
                    size=file_data['size'],
                    modified=file_data['modified'],
                    is_directory=file_data['is_directory'],
                    permissions=file_data['permissions']
                )
                for file_data in files_data
            ]
            
            return FileListResponse(
                path=path,
                files=files,
                total_count=len(files)
            )
            
    except Exception as e:
        logger.error(f"Failed to list files in {path}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list files: {str(e)}"
        )


@app.get("/files/search/{file_name}", response_model=FileListResponse)
async def search_files_by_name(
    file_name: str,
    sftp_service: SFTPService = Depends(get_sftp_service)
):
    """Search for files by name pattern."""
    try:
        with sftp_service:
            # List all files in root directory
            all_files = sftp_service.list_files(".")
            
            # Filter files that match the name pattern (case-insensitive)
            matching_files = [
                file_data for file_data in all_files
                if file_name.lower() in file_data['name'].lower()
            ]
            
            # Convert to FileInfo objects
            files = [
                FileInfo(
                    name=file_data['name'],
                    path=f"./{file_data['name']}",
                    size=file_data['size'],
                    modified=file_data['modified'],
                    is_directory=file_data['is_directory'],
                    permissions=file_data['permissions']
                )
                for file_data in matching_files
            ]
            
            return FileListResponse(
                path=".",
                files=files,
                total_count=len(files)
            )
            
    except Exception as e:
        logger.error(f"Failed to search files by name '{file_name}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search files: {str(e)}"
        )


@app.get("/file/{file_name}", response_model=FileContent)
async def get_file_by_name(
    file_name: str,
    sftp_service: SFTPService = Depends(get_sftp_service)
):
    """Get a specific file by exact name."""
    try:
        with sftp_service:
            # Check if file exists
            if not sftp_service.file_exists(file_name):
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found: {file_name}"
                )
            
            # Get file info
            file_info_data = sftp_service.get_file_info(file_name)
            
            # Skip directories
            if file_info_data['is_directory']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Path is a directory, not a file: {file_name}"
                )
            
            # Read file content
            content_bytes = sftp_service.read_file(file_name)
            
            # Detect content type
            content_type, _ = mimetypes.guess_type(file_name)
            if not content_type:
                content_type = "application/octet-stream"
            
            # Try to decode as text
            encoding = "utf-8"
            try:
                content = content_bytes.decode(encoding)
            except UnicodeDecodeError:
                # If UTF-8 fails, try other encodings
                for enc in ["latin-1", "cp1252", "iso-8859-1"]:
                    try:
                        content = content_bytes.decode(enc)
                        encoding = enc
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # If all text encodings fail, return as base64
                    import base64
                    content = base64.b64encode(content_bytes).decode('ascii')
                    encoding = "base64"
            
            file_info = FileInfo(
                name=file_info_data['name'],
                path=file_info_data['path'],
                size=file_info_data['size'],
                modified=file_info_data['modified'],
                is_directory=file_info_data['is_directory'],
                permissions=file_info_data['permissions']
            )
            
            return FileContent(
                file_info=file_info,
                content=content,
                encoding=encoding,
                content_type=content_type
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file {file_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file: {str(e)}"
        )


@app.get("/files/{file_path:path}", response_model=FileContent)
async def read_file(
    file_path: str,
    sftp_service: SFTPService = Depends(get_sftp_service)
):
    """Read and return file content."""
    try:
        with sftp_service:
            # Check if file exists
            if not sftp_service.file_exists(file_path):
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found: {file_path}"
                )
            
            # Get file info
            file_info_data = sftp_service.get_file_info(file_path)
            
            # Skip directories
            if file_info_data['is_directory']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Path is a directory, not a file: {file_path}"
                )
            
            # Read file content
            content_bytes = sftp_service.read_file(file_path)
            
            # Detect content type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = "application/octet-stream"
            
            # Try to decode as text
            encoding = "utf-8"
            try:
                content = content_bytes.decode(encoding)
            except UnicodeDecodeError:
                # If UTF-8 fails, try other encodings
                for enc in ["latin-1", "cp1252", "iso-8859-1"]:
                    try:
                        content = content_bytes.decode(enc)
                        encoding = enc
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # If all text encodings fail, return as base64
                    import base64
                    content = base64.b64encode(content_bytes).decode('ascii')
                    encoding = "base64"
            
            file_info = FileInfo(
                name=file_info_data['name'],
                path=file_info_data['path'],
                size=file_info_data['size'],
                modified=file_info_data['modified'],
                is_directory=file_info_data['is_directory'],
                permissions=file_info_data['permissions']
            )
            
            return FileContent(
                file_info=file_info,
                content=content,
                encoding=encoding,
                content_type=content_type
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if config.debug else "An unexpected error occurred"
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "obs_sftp_file_processor.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.debug
    )
