"""Main FastAPI application."""

import mimetypes
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .config import config
from .models import (
    FileContent, FileListResponse, HealthResponse, ErrorResponse, FileInfo, 
    AddSftpAchFileRequest, AddSftpAchFileResponse,
    ProcessSftpFileRequest, ProcessSftpFileResponse, ProcessSftpFileData, ProcessSftpFileErrorDetails,
    ArchivedFileListResponse, ArchivedFileContentResponse, ArchivedFileInfo,
    OracleAuthRequest, OracleAuthResponse,
    AchCorePostSpData, AchCorePostSpResponse
)
from .sftp_service import SFTPService
from .oracle_service import OracleService
from .oracle_models import AchFileCreate, AchFileUpdate, AchFileResponse, AchFileListResponse, AchFileUpdateByFileIdRequest, AchClientResponse, AchClientListResponse
from .fi_holidays_models import FiHolidayCreate, FiHolidayUpdate, FiHolidayResponse, FiHolidayListResponse
from .ach_file_lines_service import AchFileLinesService
from .ach_file_blobs_service import AchFileBlobsService
from .ach_file_blobs_models import AchFileBlobCreate, AchFileBlobResponse
from .ach_validator import parse_ach_file_content
from .file_utils import add_client_id_to_filename
from .rate_limiter import oracle_auth_rate_limiter


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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services and verify connections on application startup."""
    # Test SFTP connection and create archived folder
    try:
        sftp_service = SFTPService(config.sftp)
        with sftp_service:
            archived_folder = config.sftp.archived_folder
            sftp_service.ensure_directory_exists(archived_folder)
            logger.info(f"Archived folder '{archived_folder}' verified/created on startup")
    except Exception as e:
        logger.warning(f"Could not create archived folder on startup: {e}")
        # Don't fail startup if folder creation fails - it will be created when needed
    
    # Test Oracle connection
    try:
        logger.info("Testing Oracle database connection on startup...")
        oracle_service = OracleService(config.oracle)
        with oracle_service:
            # Test connection by getting a simple query
            with oracle_service.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                result = cursor.fetchone()
                cursor.close()
                logger.info(f"✅ Oracle connection test successful (result: {result[0]})")
                logger.info(f"   Oracle Home: {config.oracle.host}:{config.oracle.port}/{config.oracle.service_name}")
                logger.info(f"   Schema: {config.oracle.db_schema}")
    except Exception as e:
        logger.error(f"❌ Oracle connection test failed on startup: {e}")
        logger.warning("Application will continue, but Oracle operations may fail")
        # Don't fail startup - allow app to start even if Oracle is temporarily unavailable


def get_sftp_service() -> SFTPService:
    """Dependency to get SFTP service instance."""
    return SFTPService(config.sftp)


def get_oracle_service() -> OracleService:
    """Dependency to get Oracle service instance."""
    return OracleService(config.oracle)


def get_ach_file_lines_service() -> AchFileLinesService:
    """Dependency to get ACH file lines service instance."""
    return AchFileLinesService(config.oracle)


def get_ach_file_blobs_service() -> AchFileBlobsService:
    """Dependency to get ACH file blobs service instance."""
    return AchFileBlobsService(config.oracle)


def parse_file_header_record(file_content: str) -> Optional[dict]:
    """Parse File Header Record (record type '1') from ACH file content.
    
    Extracts the four required fields:
    - immediate_destination (positions 4-13)
    - immediate_destination_name (positions 41-63)
    - immediate_origin (positions 14-23)
    - immediate_origin_name (positions 64-86)
    
    Returns a dictionary with the extracted fields, or None if File Header Record not found.
    """
    if not file_content:
        return None
    
    # Split file into lines
    lines = file_content.split('\n')
    
    # Find the first non-empty line that starts with '1' (File Header Record)
    for line in lines:
        line = line.rstrip('\r')
        if not line.strip():
            continue
        
        # Check if this is a File Header Record (starts with '1')
        if len(line) >= 1 and line[0] == '1':
            # Ensure line is at least 86 characters (minimum for all required fields)
            if len(line) < 86:
                logger.warning(f"File Header Record too short: {len(line)} characters")
                return None
            
            # Extract fields based on ACH specification
            # Positions are 1-based in spec, but Python is 0-based
            immediate_destination = line[3:13].strip() if len(line) >= 13 else ""
            immediate_origin = line[13:23].strip() if len(line) >= 23 else ""
            immediate_destination_name = line[40:63].strip() if len(line) >= 63 else ""
            immediate_origin_name = line[63:86].strip() if len(line) >= 86 else ""
            
            return {
                "immediate_destination": immediate_destination,
                "immediate_destination_name": immediate_destination_name,
                "immediate_origin": immediate_origin,
                "immediate_origin_name": immediate_origin_name
            }
    
    # File Header Record not found
    logger.warning("File Header Record (record type '1') not found in file content")
    return None


def format_memo_from_file_header(file_header_data: dict) -> str:
    """Format memo string from File Header Record data.
    
    Format: Immediate Destination: [value] Immediate Destination Name: [value] 
            Immediate Origin: [value] Immediate Origin Name: [value]
    """
    return (
        f"Immediate Destination: {file_header_data.get('immediate_destination', '')} "
        f"Immediate Destination Name: {file_header_data.get('immediate_destination_name', '')} "
        f"Immediate Origin: {file_header_data.get('immediate_origin', '')} "
        f"Immediate Origin Name: {file_header_data.get('immediate_origin_name', '')}"
    )


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
    path: str = "upload",
    sftp_service: SFTPService = Depends(get_sftp_service)
):
    """List files in the specified remote directory. Defaults to 'upload' directory."""
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


@app.post("/files/addsftpachfile", response_model=AddSftpAchFileResponse)
async def add_sftp_ach_file(
    request: AddSftpAchFileRequest,
    sftp_service: SFTPService = Depends(get_sftp_service)
):
    """Upload ACH file to SFTP server using the provided filename.
    
    The filename is used exactly as provided in the request.
    """
    try:
        # Use the filename provided in the request
        filename = request.filename
        
        # Remote path - upload to the uploads directory
        remote_path = f"upload/{filename}"
        
        # Convert file contents to bytes
        file_contents_bytes = request.file_contents.encode('utf-8')
        
        with sftp_service:
            # Write file to SFTP server
            sftp_service.write_file(remote_path, file_contents_bytes)
            
            logger.info(f"Successfully uploaded ACH file to SFTP: {remote_path}")
            
            return AddSftpAchFileResponse(
                success=True,
                filename=filename,
                remote_path=remote_path,
                file_size=len(file_contents_bytes),
                message=f"File {filename} uploaded successfully to {remote_path}"
            )
            
    except Exception as e:
        logger.error(f"Failed to upload ACH file to SFTP: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file to SFTP: {str(e)}"
        )


@app.post("/files/process-sftp-file", response_model=ProcessSftpFileResponse)
async def process_sftp_file(
    request: ProcessSftpFileRequest,
    sftp_service: SFTPService = Depends(get_sftp_service),
    oracle_service: OracleService = Depends(get_oracle_service),
    ach_file_blobs_service: AchFileBlobsService = Depends(get_ach_file_blobs_service)
):
    """Process a file from the SFTP server, create database records, and archive the file.
    
    The filename is used as-is without any modifications.
    Supported file extensions: .txt, .DAT
    Example formats: ach_file_20241121.txt, AC20251105B_Generic.DAT
    """
    file_id = None
    file_blob_id = None
    renamed_filename = None
    
    try:
        # Validate client_id exists and get client_name (if not provided in request)
        client_name = request.client_name
        with oracle_service:
            clients_data = oracle_service.get_active_clients()
            # Handle both list of dicts (from service) and response object (from endpoint)
            if isinstance(clients_data, list):
                # Service returns list of dicts
                client_ids = [client['client_id'] for client in clients_data]
                # Find client_name for the given client_id if not provided in request
                if not client_name:
                    for client in clients_data:
                        if client['client_id'] == request.client_id:
                            client_name = client['client_name']
                            break
            else:
                # Response object with .clients attribute
                client_ids = [c.client_id for c in clients_data.clients]
                # Find client_name for the given client_id if not provided in request
                if not client_name:
                    for client in clients_data.clients:
                        if client.client_id == request.client_id:
                            client_name = client.client_name
                            break
            
            if request.client_id not in client_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Client ID '{request.client_id}' not found in active clients"
                )
        
        # Prepare file paths
        upload_folder = request.file_upload_folder or config.sftp.upload_folder
        archived_folder = config.sftp.archived_folder
        source_path = f"{upload_folder}/{request.file_name}" if upload_folder != "." else request.file_name
        
        # Read file from SFTP server
        with sftp_service:
            # Check if file exists
            if not sftp_service.file_exists(source_path):
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found: {source_path}"
                )
            
            # Read file content
            file_content_bytes = sftp_service.read_file(source_path)
            file_content_str = file_content_bytes.decode('utf-8')
        
        # Use original filename without any prefix
        original_filename = request.file_name
        archived_path = f"{archived_folder}/{original_filename}" if archived_folder != "." else original_filename
        
        # Set created_by_user
        created_by_user = request.created_by_user or "system-user"
        
        # Parse File Header Record and extract memo fields
        file_header_data = parse_file_header_record(file_content_str)
        memo = None
        if file_header_data:
            memo = format_memo_from_file_header(file_header_data)
            logger.info(f"Extracted File Header Record fields for memo: {memo}")
        else:
            logger.warning(f"Could not parse File Header Record from file {original_filename}, memo will not be set from file header")
        
        # If request.memo is provided, it takes precedence (or could be merged)
        # For now, use file header memo if available, otherwise use request.memo
        final_memo = memo or request.memo
        
        # Create ACH_FILES record
        try:
            with oracle_service:
                ach_file_create = AchFileCreate(
                    original_filename=original_filename,
                    processing_status="Pending",
                    file_contents=file_content_str,
                    created_by_user=created_by_user,
                    client_id=request.client_id,
                    client_name=client_name,
                    file_upload_folder=upload_folder,
                    file_upload_filename=request.file_upload_filename or request.file_name,
                    memo=final_memo
                )
                file_id = oracle_service.create_ach_file(ach_file_create)
                logger.info(f"Created ACH_FILES record with ID: {file_id}")
        except Exception as e:
            logger.error(f"Failed to create ACH_FILES record: {e}")
            return ProcessSftpFileResponse(
                success=False,
                message="Failed to create ACH_FILES record",
                error=str(e),
                details=ProcessSftpFileErrorDetails(
                    file_id=None,
                    file_blob_id=None,
                    processing_status="Failed",
                    stage="file_creation"
                )
            )
        
        # Create ACH_FILES_BLOBS record
        try:
            with ach_file_blobs_service:
                ach_file_blob_create = AchFileBlobCreate(
                    file_id=file_id,
                    original_filename=original_filename,
                    processing_status="Pending",
                    file_contents=file_content_str,
                    created_by_user=created_by_user,
                    client_id=request.client_id,
                    client_name=client_name,
                    file_upload_folder=upload_folder,
                    file_upload_filename=request.file_upload_filename or request.file_name,
                    memo=final_memo
                )
                file_blob_id = ach_file_blobs_service.create_ach_file_blob(ach_file_blob_create)
                logger.info(f"Created ACH_FILES_BLOBS record with ID: {file_blob_id}")
        except Exception as e:
            logger.error(f"Failed to create ACH_FILES_BLOBS record: {e}")
            # Update BLOB status to Failed
            try:
                with ach_file_blobs_service:
                    if file_blob_id:
                        ach_file_blobs_service.update_ach_file_blob_status(
                            file_blob_id, "Failed", created_by_user
                        )
            except Exception as update_error:
                logger.error(f"Failed to update BLOB status: {update_error}")
            
            return ProcessSftpFileResponse(
                success=False,
                message="Failed to create ACH_FILES_BLOBS record",
                error=str(e),
                details=ProcessSftpFileErrorDetails(
                    file_id=file_id,
                    file_blob_id=file_blob_id,
                    processing_status="Failed",
                    stage="blob_creation"
                )
            )
        
        # Update BLOB status to Completed
        try:
            with ach_file_blobs_service:
                ach_file_blobs_service.update_ach_file_blob_status(
                    file_blob_id, "Completed", created_by_user
                )
        except Exception as e:
            logger.warning(f"Failed to update BLOB status to Completed: {e}")
            # Continue anyway - BLOB was created successfully
        
        # Move file to archived folder
        try:
            with sftp_service:
                # Ensure archived folder exists
                sftp_service.ensure_directory_exists(archived_folder)
                
                # Move file
                sftp_service.move_file(source_path, archived_path)
                logger.info(f"Moved file from {source_path} to {archived_path}")
        except Exception as e:
            logger.error(f"Failed to move file to archived folder: {e}")
            # File and BLOB were created successfully, but move failed
            # Return partial success with warning
            return ProcessSftpFileResponse(
                success=True,
                message=f"File processed successfully, but failed to move to archived folder: {str(e)}",
                data=ProcessSftpFileData(
                    file_id=file_id,
                    file_blob_id=file_blob_id,
                    original_filename=original_filename,
                    renamed_filename=original_filename,
                    processing_status="Completed",
                    archived_path=archived_path
                )
            )
        
        # Success
        return ProcessSftpFileResponse(
            success=True,
            message="File processed successfully",
            data=ProcessSftpFileData(
                file_id=file_id,
                file_blob_id=file_blob_id,
                original_filename=original_filename,
                renamed_filename=original_filename,
                processing_status="Completed",
                archived_path=archived_path
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process SFTP file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(e)}"
        )


@app.get("/files/archived", response_model=ArchivedFileListResponse)
async def list_archived_files(
    limit: int = 100,
    offset: int = 0,
    sftp_service: SFTPService = Depends(get_sftp_service)
):
    """List all files in the Archived folder on the SFTP server."""
    try:
        archived_folder = config.sftp.archived_folder
        
        with sftp_service:
            # Ensure archived folder exists
            sftp_service.ensure_directory_exists(archived_folder)
            
            # List files in archived folder
            files_data = sftp_service.list_files(archived_folder)
            
            # Filter out directories and sort by modified date (descending)
            file_list = [
                f for f in files_data 
                if not f['is_directory']
            ]
            file_list.sort(key=lambda x: x['modified'], reverse=True)
            
            # Apply pagination
            total = len(file_list)
            paginated_files = file_list[offset:offset + limit]
            
            # Convert to response format
            archived_files = [
                ArchivedFileInfo(
                    name=f['name'],
                    size=f['size'],
                    created_date=None,  # SFTP doesn't always provide creation date
                    modified_date=datetime.fromtimestamp(f['modified'])
                )
                for f in paginated_files
            ]
            
            return ArchivedFileListResponse(
                files=archived_files,
                total=total,
                limit=limit,
                offset=offset
            )
            
    except Exception as e:
        logger.error(f"Failed to list archived files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list archived files: {str(e)}"
        )


@app.get("/files/archived/{file_name}", response_model=ArchivedFileContentResponse)
async def get_archived_file(
    file_name: str,
    sftp_service: SFTPService = Depends(get_sftp_service)
):
    """Retrieve content of an archived file."""
    try:
        archived_folder = config.sftp.archived_folder
        file_path = f"{archived_folder}/{file_name}" if archived_folder != "." else file_name
        
        with sftp_service:
            # Ensure archived folder exists
            sftp_service.ensure_directory_exists(archived_folder)
            
            # Check if file exists
            if not sftp_service.file_exists(file_path):
                raise HTTPException(
                    status_code=404,
                    detail=f"Archived file not found: {file_name}"
                )
            
            # Read file content
            content_bytes = sftp_service.read_file(file_path)
            
            # Try to decode as text
            try:
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # If UTF-8 fails, try other encodings
                for enc in ["latin-1", "cp1252", "iso-8859-1"]:
                    try:
                        content = content_bytes.decode(enc)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # If all text encodings fail, return as base64
                    import base64
                    content = base64.b64encode(content_bytes).decode('ascii')
            
            return ArchivedFileContentResponse(
                file_name=file_name,
                content=content,
                size=len(content_bytes)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get archived file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get archived file: {str(e)}"
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


# Oracle Database Endpoints

@app.get("/oracle/ach-files", response_model=AchFileListResponse)
async def get_ach_files(
    limit: int = 100,
    offset: int = 0,
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """Get list of ACH_FILES records.
    
    Excludes files starting with 'FEDACHOUT' or ending with '.pdf'.
    
    Args:
        limit: Maximum number of records to return (default: 100)
        offset: Number of records to skip (default: 0)
    """
    try:
        with oracle_service:
            files = oracle_service.get_ach_files(limit=limit, offset=offset)
            total_count = oracle_service.get_ach_files_count()
            
            return AchFileListResponse(
                files=files,
                total_count=total_count
            )
            
    except Exception as e:
        logger.error(f"Failed to get ACH_FILES: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ACH_FILES: {str(e)}"
        )


@app.get("/oracle/ach-files/{file_id}", response_model=AchFileResponse)
async def get_ach_file(
    file_id: int,
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """Get a specific ACH_FILES record by ID."""
    try:
        with oracle_service:
            ach_file = oracle_service.get_ach_file(file_id)
            
            if not ach_file:
                raise HTTPException(
                    status_code=404,
                    detail=f"ACH_FILES record not found: {file_id}"
                )
            
            return ach_file
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ACH_FILES record {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ACH_FILES record: {str(e)}"
        )


@app.get("/oracle/ach-files/{file_id}/download")
async def download_ach_file_blob(
    file_id: int,
    ach_file_blobs_service: AchFileBlobsService = Depends(get_ach_file_blobs_service)
):
    """Download file from ACH_FILES_BLOBS by FILE_ID with original filename."""
    try:
        with ach_file_blobs_service:
            file_blob = ach_file_blobs_service.get_ach_file_blob_by_file_id(file_id)
            
            if not file_blob:
                raise HTTPException(
                    status_code=404,
                    detail=f"ACH_FILES_BLOBS record not found for FILE_ID: {file_id}"
                )
            
            if not file_blob.file_contents:
                raise HTTPException(
                    status_code=404,
                    detail=f"File contents not found for FILE_ID: {file_id}"
                )
            
            # Return file as downloadable response with original filename
            return Response(
                content=file_blob.file_contents.encode('utf-8'),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f'attachment; filename="{file_blob.original_filename}"'
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download ACH_FILES_BLOBS for FILE_ID {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download file: {str(e)}"
        )


@app.get("/oracle/ach-files-blobs/{file_blob_id}", response_model=AchFileBlobResponse)
async def get_ach_file_blob(
    file_blob_id: int,
    ach_file_blobs_service: AchFileBlobsService = Depends(get_ach_file_blobs_service)
):
    """Get a specific ACH_FILES_BLOBS record by FILE_BLOB_ID."""
    try:
        with ach_file_blobs_service:
            file_blob = ach_file_blobs_service.get_ach_file_blob(file_blob_id)
            
            if not file_blob:
                raise HTTPException(
                    status_code=404,
                    detail=f"ACH_FILES_BLOBS record not found: {file_blob_id}"
                )
            
            return file_blob
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ACH_FILES_BLOBS record {file_blob_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ACH_FILES_BLOBS record: {str(e)}"
        )


@app.get("/oracle/ach-files-blobs/file-id/{file_id}", response_model=AchFileBlobResponse)
async def get_ach_file_blob_by_file_id(
    file_id: int,
    ach_file_blobs_service: AchFileBlobsService = Depends(get_ach_file_blobs_service)
):
    """Get ACH_FILES_BLOBS record by FILE_ID."""
    try:
        with ach_file_blobs_service:
            file_blob = ach_file_blobs_service.get_ach_file_blob_by_file_id(file_id)
            
            if not file_blob:
                raise HTTPException(
                    status_code=404,
                    detail=f"ACH_FILES_BLOBS record not found for FILE_ID: {file_id}"
                )
            
            return file_blob
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ACH_FILES_BLOBS record by FILE_ID {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ACH_FILES_BLOBS record: {str(e)}"
        )


@app.post("/oracle/ach-files", response_model=AchFileResponse)
async def create_ach_file(
    ach_file: AchFileCreate,
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """Create a new ACH_FILES record."""
    try:
        with oracle_service:
            file_id = oracle_service.create_ach_file(ach_file)
            created_file = oracle_service.get_ach_file(file_id)
            
            return created_file
            
    except Exception as e:
        logger.error(f"Failed to create ACH_FILES record: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create ACH_FILES record: {str(e)}"
        )


@app.put("/oracle/ach-files/{file_id}", response_model=AchFileResponse)
async def update_ach_file(
    file_id: int,
    ach_file: AchFileUpdate,
    user: Optional[str] = None,
    processing_status: Optional[str] = None,
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """Update an ACH_FILES record.
    
    Args:
        file_id: The ID of the ACH_FILES record to update
        ach_file: The update data (processing_status, file_contents, etc.)
        user: Optional user parameter to set UPDATED_BY_USER column. 
              If provided, takes precedence over updated_by_user in request body.
        processing_status: Optional parameter to set PROCESSING_STATUS column to "Approved".
                           If provided, takes precedence over processing_status in request body.
    """
    try:
        with oracle_service:
            # If user query parameter is provided, override updated_by_user in body
            if user is not None:
                ach_file.updated_by_user = user
            
            # If processing_status query parameter is provided, set processing_status to "Approved"
            if processing_status is not None:
                ach_file.processing_status = "Approved"
            
            success = oracle_service.update_ach_file(file_id, ach_file)
            
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"ACH_FILES record not found: {file_id}"
                )
            
            updated_file = oracle_service.get_ach_file(file_id)
            return updated_file
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update ACH_FILES record {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update ACH_FILES record: {str(e)}"
        )


@app.post("/oracle/ach-files-update-by-file-id/{file_id}")
async def update_ach_file_by_file_id(
    file_id: int,
    request: AchFileUpdateByFileIdRequest,
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """Update ACH_FILES record by file_id with file_contents, updated_by_user, and updated_date.
    
    Also parses the file contents and inserts records into appropriate ACH record type tables:
    - ACH_FILE_HEADER (record type 1)
    - ACH_BATCH_HEADER (record type 5)
    - ACH_ENTRY_DETAIL (record type 6)
    - ACH_ADDENDA (record type 7)
    - ACH_BATCH_CONTROL (record type 8)
    - ACH_FILE_CONTROL (record type 9)
    """
    try:
        with oracle_service:
            # First, delete existing records for this file_id to avoid duplicates
            # (This ensures clean re-processing if the file is updated)
            try:
                with oracle_service.get_connection() as conn:
                    cursor = conn.cursor()
                    # Delete in reverse order of dependencies
                    cursor.execute("DELETE FROM ACH_ADDENDA WHERE FILE_ID = :file_id", {'file_id': file_id})
                    cursor.execute("DELETE FROM ACH_ENTRY_DETAIL WHERE FILE_ID = :file_id", {'file_id': file_id})
                    cursor.execute("DELETE FROM ACH_BATCH_CONTROL WHERE FILE_ID = :file_id", {'file_id': file_id})
                    cursor.execute("DELETE FROM ACH_BATCH_HEADER WHERE FILE_ID = :file_id", {'file_id': file_id})
                    cursor.execute("DELETE FROM ACH_FILE_CONTROL WHERE FILE_ID = :file_id", {'file_id': file_id})
                    cursor.execute("DELETE FROM ACH_FILE_HEADER WHERE FILE_ID = :file_id", {'file_id': file_id})
                    conn.commit()
                    logger.info(f"Deleted existing ACH records for file_id {file_id}")
            except Exception as e:
                logger.warning(f"Failed to delete existing records (may not exist): {e}")
                # Continue anyway - records may not exist yet
            
            # Update the ACH_FILES record
            success = oracle_service.update_ach_file_by_file_id(
                file_id=file_id,
                file_contents=request.file_contents,
                updated_by_user=request.updated_by_user,
                updated_date=request.updated_date
            )
            
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"ACH_FILES record not found: {file_id}"
                )
            
            # Parse and insert ACH records into appropriate tables
            try:
                record_counts = oracle_service.parse_and_insert_ach_records(
                    file_id=file_id,
                    file_contents=request.file_contents
                )
                logger.info(f"Successfully parsed and inserted ACH records for file_id {file_id}: {record_counts}")
            except Exception as e:
                logger.error(f"Failed to parse and insert ACH records for file_id {file_id}: {e}")
                # Don't fail the entire request - file was updated successfully
                # Just log the error
            
            # Get the updated record
            updated_file = oracle_service.get_ach_file(file_id)
            return updated_file
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update ACH_FILES record {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update ACH_FILES record: {str(e)}"
        )


@app.get("/api/oracle/get-ach-data-for-core-post-sp-approved", response_model=AchCorePostSpResponse)
async def get_ach_data_for_core_post_sp_approved(
    file_id: Optional[int] = None,
    client_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """Get ACH data for Core Post Stored Procedure (approved files only).
    
    Returns entry detail records with all related data needed for the stored procedure
    BE_K_INTERFAZ_ACH.BE_P_PROCESA_PAGO. Only includes records from files with
    PROCESSING_STATUS = 'APPROVED'.
    
    Query Parameters:
        file_id: Optional filter by specific file_id
        client_id: Optional filter by specific client_id
        limit: Optional limit number of records (for pagination)
        offset: Optional offset for pagination
    
    Returns:
        List of ACH data records with all fields needed for the stored procedure
    """
    try:
        with oracle_service:
            results = oracle_service.get_ach_data_for_core_post_sp_approved(
                file_id=file_id,
                client_id=client_id,
                limit=limit,
                offset=offset
            )
            
            # Convert to response models
            data = []
            for record in results:
                data.append(AchCorePostSpData(
                    trace_sequence_number=record.get('trace_sequence_number'),
                    client_id=record.get('client_id'),
                    origin_agency=record.get('origin_agency'),
                    origin_sub_account=record.get('origin_sub_account', 0),
                    ach_class=record.get('ach_class'),
                    origin_account=record.get('origin_account'),
                    company_id=record.get('company_id'),
                    company_entry_description=record.get('company_entry_description'),
                    receiver_routing_aba=record.get('receiver_routing_aba'),
                    receiver_account=record.get('receiver_account'),
                    transaction_code=record.get('transaction_code'),
                    company_name=record.get('company_name'),
                    receiver_id=record.get('receiver_id'),
                    receiver_name=record.get('receiver_name'),
                    reference_code=record.get('reference_code'),
                    payment_description=record.get('payment_description'),
                    amount=record.get('amount'),
                    entry_detail_id=record.get('entry_detail_id'),
                    file_id=record.get('file_id'),
                    batch_number=record.get('batch_number'),
                    original_filename=record.get('original_filename')
                ))
            
            return AchCorePostSpResponse(
                success=True,
                data=data,
                total_count=len(data),
                message=f"Retrieved {len(data)} ACH records for Core Post SP"
            )
            
    except Exception as e:
        logger.error(f"Failed to get ACH data for Core Post SP: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve ACH data: {str(e)}"
        )


@app.delete("/oracle/ach-files/{file_id}")
async def delete_ach_file(
    file_id: int,
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """Delete an ACH_FILES record."""
    try:
        with oracle_service:
            success = oracle_service.delete_ach_file(file_id)
            
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"ACH_FILES record not found: {file_id}"
                )
            
            return {"message": f"ACH_FILES record {file_id} deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete ACH_FILES record {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete ACH_FILES record: {str(e)}"
        )


# ==================== FI_HOLIDAYS Endpoints ====================

@app.get("/oracle/fi-holidays", response_model=FiHolidayListResponse)
async def get_fi_holidays(
    limit: int = 100,
    offset: int = 0,
    is_active: Optional[int] = None,
    year: Optional[int] = None,
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """Get list of FI_HOLIDAYS records.
    
    Args:
        limit: Maximum number of records to return (default: 100)
        offset: Number of records to skip (default: 0)
        is_active: Filter by active status (1=active, 0=inactive, None=all)
        year: Filter by year (e.g., 2024)
    """
    try:
        with oracle_service:
            holidays = oracle_service.get_fi_holidays(
                limit=limit,
                offset=offset,
                is_active=is_active,
                year=year
            )
            total_count = oracle_service.get_fi_holidays_count(
                is_active=is_active,
                year=year
            )
            
            return FiHolidayListResponse(
                holidays=holidays,
                total_count=total_count
            )
            
    except Exception as e:
        logger.error(f"Failed to get FI_HOLIDAYS: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get FI_HOLIDAYS: {str(e)}"
        )


@app.get("/oracle/fi-holidays/{holiday_id}", response_model=FiHolidayResponse)
async def get_fi_holiday(
    holiday_id: int,
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """Get a specific FI_HOLIDAYS record by ID."""
    try:
        with oracle_service:
            holiday = oracle_service.get_fi_holiday(holiday_id)
            
            if not holiday:
                raise HTTPException(
                    status_code=404,
                    detail=f"FI_HOLIDAYS record not found: {holiday_id}"
                )
            
            return holiday
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get FI_HOLIDAYS record {holiday_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get FI_HOLIDAYS record: {str(e)}"
        )


@app.post("/oracle/fi-holidays", response_model=FiHolidayResponse)
async def create_fi_holiday(
    holiday: FiHolidayCreate,
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """Create a new FI_HOLIDAYS record."""
    try:
        with oracle_service:
            holiday_id = oracle_service.create_fi_holiday(holiday)
            
            # Get the created record
            created_holiday = oracle_service.get_fi_holiday(holiday_id)
            return created_holiday
            
    except Exception as e:
        logger.error(f"Failed to create FI_HOLIDAYS record: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create FI_HOLIDAYS record: {str(e)}"
        )


@app.put("/oracle/fi-holidays/{holiday_id}", response_model=FiHolidayResponse)
async def update_fi_holiday(
    holiday_id: int,
    holiday: FiHolidayUpdate,
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """Update a FI_HOLIDAYS record.
    
    Args:
        holiday_id: The ID of the FI_HOLIDAYS record to update
        holiday: The update data (holiday_date, holiday_name, is_active, etc.)
    """
    try:
        with oracle_service:
            success = oracle_service.update_fi_holiday(holiday_id, holiday)
            
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"FI_HOLIDAYS record not found: {holiday_id}"
                )
            
            # Get the updated record
            updated_holiday = oracle_service.get_fi_holiday(holiday_id)
            return updated_holiday
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update FI_HOLIDAYS record {holiday_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update FI_HOLIDAYS record: {str(e)}"
        )


@app.delete("/oracle/fi-holidays/{holiday_id}")
async def delete_fi_holiday(
    holiday_id: int,
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """Delete a FI_HOLIDAYS record."""
    try:
        with oracle_service:
            success = oracle_service.delete_fi_holiday(holiday_id)
            
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"FI_HOLIDAYS record not found: {holiday_id}"
                )
            
            return {"message": f"FI_HOLIDAYS record {holiday_id} deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete FI_HOLIDAYS record {holiday_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete FI_HOLIDAYS record: {str(e)}"
        )


@app.get("/oracle/clients", response_model=AchClientListResponse)
async def get_active_clients(
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """Get active clients from ACH_CLIENTS table where CLIENT_STATUS = 'Active'."""
    try:
        with oracle_service:
            clients_data = oracle_service.get_active_clients()
            
            clients = [
                AchClientResponse(
                    client_id=client['client_id'],
                    client_name=client['client_name']
                )
                for client in clients_data
            ]
            
            return AchClientListResponse(
                clients=clients,
                total_count=len(clients)
            )
            
    except Exception as e:
        logger.error(f"Failed to get active clients: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active clients: {str(e)}"
        )


@app.post("/oracle-auth", response_model=OracleAuthResponse)
async def oracle_auth(
    request: OracleAuthRequest,
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """
    Check if email and password hash match in API_USERS table.
    
    Returns authenticated (true/false) and is_admin flag.
    Rate limited to 15 requests per minute per email.
    """
    try:
        # Check rate limit
        is_allowed, remaining = oracle_auth_rate_limiter.is_allowed(request.email)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for email: {request.email}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum 15 requests per minute per email. Please try again later."
            )
        
        # Check email and password hash in database
        with oracle_service:
            auth_result = oracle_service.check_email_password_hash(
                email=request.email,
                password_hash=request.password_hash
            )
        
        logger.info(f"Oracle auth check for {request.email}: {'Authenticated' if auth_result['authenticated'] else 'Not authenticated'} (IS_ADMIN: {auth_result['is_admin']}, remaining requests: {remaining})")
        
        return OracleAuthResponse(
            authenticated=auth_result['authenticated'],
            is_admin=auth_result['is_admin']
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like rate limit)
        raise
    except Exception as e:
        logger.error(f"Failed to check email and password hash: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check authentication: {str(e)}"
        )


@app.post("/sync/sftp-to-oracle")
async def sync_sftp_to_oracle(
    oracle_service: OracleService = Depends(get_oracle_service),
    sftp_service: SFTPService = Depends(get_sftp_service)
):
    """Sync all SFTP files to Oracle ACH_FILES table."""
    try:
        results = {
            'total_files': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'errors': []
        }
        
        with oracle_service, sftp_service:
            # Get list of files from SFTP upload directory
            sftp_files = sftp_service.list_files("upload")
            results['total_files'] = len(sftp_files)
            
            # Process each file
            for file_data in sftp_files:
                filename = file_data['name']
                
                # Skip directories
                if file_data['is_directory']:
                    continue
                
                try:
                    # Get file content - use full path from upload directory
                    file_path = f"upload/{filename}"
                    content_bytes = sftp_service.read_file(file_path)
                    
                    # Try to decode as text
                    try:
                        content = content_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        # If UTF-8 fails, try other encodings
                        for enc in ["latin-1", "cp1252", "iso-8859-1"]:
                            try:
                                content = content_bytes.decode(enc)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # If all text encodings fail, skip the file
                            results['errors'].append(f"Could not decode file {filename}")
                            results['failed_syncs'] += 1
                            continue
                    
                    # Create ACH_FILES record
                    ach_file = AchFileCreate(
                        original_filename=filename,
                        processing_status="Pending",
                        file_contents=content,
                        created_by_user="UnityBankUserName@UB.com"
                    )
                    
                    # Insert into Oracle
                    file_id = oracle_service.create_ach_file(ach_file)
                    
                    logger.info(f"Successfully synced {filename} to Oracle with ID: {file_id}")
                    results['successful_syncs'] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to sync {filename}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['failed_syncs'] += 1
        
        return results
        
    except Exception as e:
        logger.error(f"Sync process failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Sync process failed: {str(e)}"
        )


@app.post("/run-sync-process")
async def run_sync_process(
    oracle_service: OracleService = Depends(get_oracle_service),
    sftp_service: SFTPService = Depends(get_sftp_service),
    ach_file_lines_service: AchFileLinesService = Depends(get_ach_file_lines_service)
):
    """Run the complete SFTP to Oracle sync and ACH processing."""
    try:
        logger.info("Starting complete sync process via API")
        
        results = {
            'sync_results': {
                'total_files': 0,
                'successful_syncs': 0,
                'failed_syncs': 0,
                'errors': []
            },
            'line_results': {
                'files_processed': 0,
                'total_lines_created': 0,
                'files_with_errors': 0,
                'errors': []
            }
        }
        
        # Step 1: SFTP to Oracle Sync
        with oracle_service, sftp_service:
            # Get list of files from SFTP upload directory
            sftp_files = sftp_service.list_files("upload")
            results['sync_results']['total_files'] = len(sftp_files)
            
            # Process each file
            for file_data in sftp_files:
                filename = file_data['name']
                
                # Skip directories
                if file_data['is_directory']:
                    continue
                
                try:
                    # Get file content - use full path from upload directory
                    file_path = f"upload/{filename}"
                    content_bytes = sftp_service.read_file(file_path)
                    
                    # Try to decode as text
                    try:
                        content = content_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        # If UTF-8 fails, try other encodings
                        for enc in ["latin-1", "cp1252", "iso-8859-1"]:
                            try:
                                content = content_bytes.decode(enc)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # If all text encodings fail, skip the file
                            results['sync_results']['errors'].append(f"Could not decode file {filename}")
                            results['sync_results']['failed_syncs'] += 1
                            continue
                    
                    # Create ACH_FILES record
                    ach_file = AchFileCreate(
                        original_filename=filename,
                        processing_status="Pending",
                        file_contents=content,
                        created_by_user="UnityBankUserName@UB.com"
                    )
                    
                    # Insert into Oracle
                    file_id = oracle_service.create_ach_file(ach_file)
                    
                    logger.info(f"Successfully synced {filename} to Oracle with ID: {file_id}")
                    results['sync_results']['successful_syncs'] += 1
                    
                except Exception as e:
                    error_msg = f"Failed to sync {filename}: {e}"
                    logger.error(error_msg)
                    results['sync_results']['errors'].append(error_msg)
                    results['sync_results']['failed_syncs'] += 1
        
        # Step 2: Process ACH File Lines
        with oracle_service, ach_file_lines_service:
            # Get all files with status 'Pending'
            all_files = oracle_service.get_ach_files(limit=1000)
            pending_files = [f for f in all_files if f.processing_status == 'Pending']
            
            logger.info(f"Found {len(pending_files)} files with status 'Pending'")
            
            for ach_file in pending_files:
                try:
                    logger.info(f"Processing file: {ach_file.original_filename} (ID: {ach_file.file_id})")
                    
                    # Parse and validate ACH file content
                    line_validations = parse_ach_file_content(ach_file.file_contents)
                    
                    # Delete existing lines for this file
                    deleted_count = ach_file_lines_service.delete_lines_by_file_id(ach_file.file_id)
                    logger.info(f"Deleted {deleted_count} existing ACH_FILE_LINES records")
                    
                    # Prepare batch data for insertion
                    batch_data = []
                    
                    for validation in line_validations:
                        line_data = {
                            'line_number': validation.line_number,
                            'line_content': validation.line_content,
                            'line_errors': '; '.join(validation.errors) if validation.errors else None,
                            'created_by_user': 'UnityBankUserName@UB.com'
                        }
                        batch_data.append(line_data)
                    
                    # Insert all lines in batch
                    if batch_data:
                        lines_created = ach_file_lines_service.create_ach_file_lines_batch(ach_file.file_id, batch_data)
                        results['line_results']['total_lines_created'] += lines_created
                        logger.info(f"Created {lines_created} ACH_FILE_LINES records")
                    
                    # Update file status to 'Processed'
                    update_data = AchFileUpdate(
                        processing_status='Processed',
                        updated_by_user='UnityBankUserName@UB.com'
                    )
                    oracle_service.update_ach_file(ach_file.file_id, update_data)
                    
                    results['line_results']['files_processed'] += 1
                    logger.info(f"Successfully processed {ach_file.original_filename}: {lines_created} lines created")
                    
                except Exception as e:
                    error_msg = f"Failed to process file {ach_file.original_filename} (ID: {ach_file.file_id}): {e}"
                    logger.error(error_msg)
                    results['line_results']['errors'].append(error_msg)
                    results['line_results']['files_with_errors'] += 1
        
        # Check if process was successful
        total_successful = results['sync_results']['successful_syncs'] + results['line_results']['files_processed']
        total_errors = len(results['sync_results']['errors']) + len(results['line_results']['errors'])
        
        if total_successful > 0 and total_errors == 0:
            return {
                "status": "Successfully Executed",
                "message": f"Sync process completed successfully. {results['sync_results']['successful_syncs']} files synced, {results['line_results']['files_processed']} files processed, {results['line_results']['total_lines_created']} lines created.",
                "details": results
            }
        elif total_successful > 0:
            return {
                "status": "Partially Successful",
                "message": f"Sync process completed with some errors. {results['sync_results']['successful_syncs']} files synced, {results['line_results']['files_processed']} files processed, {results['line_results']['total_lines_created']} lines created.",
                "details": results
            }
        else:
            return {
                "status": "Failed",
                "message": "Sync process failed with no successful operations.",
                "details": results
            }
        
    except Exception as e:
        logger.error(f"Sync process failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Sync process failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "obs_sftp_file_processor.main:app",
        host="0.0.0.0",
        port=8002,
        reload=config.debug
    )
