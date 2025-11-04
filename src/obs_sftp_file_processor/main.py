"""Main FastAPI application."""

import mimetypes
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from loguru import logger

from .config import config
from .models import FileContent, FileListResponse, HealthResponse, ErrorResponse, FileInfo, AddSftpAchFileRequest, AddSftpAchFileResponse
from .sftp_service import SFTPService
from .oracle_service import OracleService
from .oracle_models import AchFileCreate, AchFileUpdate, AchFileResponse, AchFileListResponse, AchFileUpdateByFileIdRequest, AchClientResponse, AchClientListResponse
from .ach_file_lines_service import AchFileLinesService
from .ach_validator import parse_ach_file_content


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


def get_oracle_service() -> OracleService:
    """Dependency to get Oracle service instance."""
    return OracleService(config.oracle)


def get_ach_file_lines_service() -> AchFileLinesService:
    """Dependency to get ACH file lines service instance."""
    return AchFileLinesService(config.oracle)


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
    """Upload ACH file to SFTP server with filename pattern CLIENTID_{CLIENTID}_FED_ACH_FILE_{YYMMDDHHSS}.txt"""
    try:
        # Generate filename with pattern: CLIENTID_{CLIENTID}_FED_ACH_FILE_{YYMMDDHHSS}.txt
        # YYMMDDHHSS format: YY (year), MM (month), DD (day), HH (hour), MM (minute) = 10 digits
        timestamp = datetime.now().strftime("%y%m%d%H%M")
        filename = f"CLIENTID_{request.client_id}_FED_ACH_FILE_{timestamp}.txt"
        
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
    """Get list of ACH_FILES records."""
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
    oracle_service: OracleService = Depends(get_oracle_service)
):
    """Update an ACH_FILES record."""
    try:
        with oracle_service:
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
    """Update ACH_FILES record by file_id with file_contents, updated_by_user, and updated_date."""
    try:
        with oracle_service:
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
        port=8000,
        reload=config.debug
    )
