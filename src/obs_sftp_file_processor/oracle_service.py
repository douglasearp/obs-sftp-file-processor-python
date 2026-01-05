"""Oracle database service for ACH_FILES table operations."""

import os
import oracledb
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
import bcrypt
from .oracle_config import OracleConfig
from .oracle_models import AchFileCreate, AchFileUpdate, AchFileResponse
from .fi_holidays_models import FiHolidayCreate, FiHolidayUpdate, FiHolidayResponse
from .ach_account_swaps_models import AchAccountSwapCreate, AchAccountSwapUpdate, AchAccountSwapResponse, SwapLookupResponse
from .ach_record_models import (
    AchFileHeaderCreate,
    AchBatchHeaderCreate,
    AchEntryDetailCreate,
    AchAddendaCreate,
    AchBatchControlCreate,
    AchFileControlCreate
)


class OracleService:
    """Service for Oracle database operations."""
    
    def __init__(self, config: OracleConfig):
        """Initialize Oracle service with configuration."""
        self.config = config
        self.pool: Optional[oracledb.ConnectionPool] = None
    
    def connect(self) -> None:
        """Establish Oracle connection pool.
        
        Uses thin mode by default (no Oracle Instant Client required).
        If ORACLE_HOME is set, will attempt to use thick mode for encryption support.
        """
        try:
            # Check if Oracle Instant Client is available (thick mode)
            oracle_home = os.environ.get('ORACLE_HOME')
            use_thick_mode = False
            
            if oracle_home:
                try:
                    oracledb.init_oracle_client(lib_dir=oracle_home)
                    logger.info(f"Using Oracle thick mode (ORACLE_HOME={oracle_home})")
                    use_thick_mode = True
                except Exception as e:
                    logger.warning(f"Thick mode initialization failed: {e}")
                    logger.info("Falling back to thin mode")
                    # Try without lib_dir
                    try:
                        oracledb.init_oracle_client()
                        logger.info("Oracle thick mode initialized without lib_dir")
                        use_thick_mode = True
                    except Exception as e2:
                        logger.warning(f"Thick mode fallback failed: {e2}")
                        logger.info("Using thin mode (no encryption support)")
                        # Don't raise - continue with thin mode
            else:
                logger.info("Using Oracle thin mode (no Instant Client required)")
            
            # Create connection pool with optional TLS/SSL configuration
            pool_params = {
                'user': self.config.username,
                'password': self.config.password,
                'dsn': self.config.dsn,
                'min': self.config.min_pool_size,
                'max': self.config.max_pool_size,
                'increment': self.config.pool_increment
            }
            
            # Add TLS/SSL configuration if provided
            if self.config.config_dir:
                pool_params['config_dir'] = self.config.config_dir
                logger.info(f"Using Oracle config directory: {self.config.config_dir}")
            
            if self.config.wallet_location:
                pool_params['wallet_location'] = self.config.wallet_location
                logger.info(f"Using Oracle wallet location: {self.config.wallet_location}")
            
            self.pool = oracledb.create_pool(**pool_params)
            logger.info("Oracle connection pool established successfully")
            
        except Exception as e:
            logger.error(f"Failed to create Oracle connection pool: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close Oracle connection pool."""
        if self.pool:
            self.pool.close()
            self.pool = None
            logger.info("Oracle connection pool closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def get_connection(self):
        """Get a connection from the pool."""
        if not self.pool:
            raise RuntimeError("Oracle connection pool not established")
        return self.pool.acquire()
    
    def create_ach_file(self, ach_file: AchFileCreate) -> int:
        """Create a new ACH_FILES record.
        
        For large CLOB inserts (>1MB), uses DBMS_LOB to reduce PGA memory usage.
        This prevents ORA-04036 errors when inserting large file contents.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check file size to determine if we need DBMS_LOB approach
                # Use more conservative threshold (500KB) and check both string length and encoded size
                if ach_file.file_contents:
                    char_length = len(ach_file.file_contents)
                    byte_size = len(ach_file.file_contents.encode('utf-8'))
                    file_contents_size = max(char_length, byte_size)
                else:
                    file_contents_size = 0
                # Lower threshold to 500KB to be more conservative and prevent edge cases
                use_lob_insert = file_contents_size > 512 * 1024  # 500KB threshold
                
                if use_lob_insert and ach_file.file_contents:
                    # For large CLOBs, insert with empty CLOB first, then write using DBMS_LOB
                    insert_plsql = """
                    DECLARE
                        v_file_id NUMBER;
                        v_clob CLOB;
                    BEGIN
                        INSERT INTO ACH_FILES (
                            ORIGINAL_FILENAME,
                            PROCESSING_STATUS,
                            FILE_CONTENTS,
                            CREATED_BY_USER,
                            CREATED_DATE,
                            CLIENT_ID,
                            CLIENT_NAME,
                            FILE_UPLOAD_FOLDER,
                            FILE_UPLOAD_FILENAME,
                            MEMO
                        ) VALUES (
                            :original_filename,
                            :processing_status,
                            EMPTY_CLOB(),
                            :created_by_user,
                            CURRENT_TIMESTAMP,
                            :client_id,
                            :client_name,
                            :file_upload_folder,
                            :file_upload_filename,
                            :memo
                        ) RETURNING FILE_ID, FILE_CONTENTS INTO v_file_id, v_clob;
                        
                        :file_id := v_file_id;
                        :file_contents_clob := v_clob;
                    END;
                    """
                    
                    # Execute insert with empty CLOB
                    file_id = cursor.var(int)
                    file_contents_clob = cursor.var(oracledb.DB_TYPE_CLOB)
                    cursor.execute(insert_plsql, {
                        'original_filename': ach_file.original_filename,
                        'processing_status': ach_file.processing_status,
                        'created_by_user': ach_file.created_by_user,
                        'client_id': ach_file.client_id,
                        'client_name': ach_file.client_name,
                        'file_upload_folder': ach_file.file_upload_folder,
                        'file_upload_filename': ach_file.file_upload_filename,
                        'memo': ach_file.memo,
                        'file_id': file_id,
                        'file_contents_clob': file_contents_clob
                    })
                    
                    # Get the CLOB locator
                    clob = file_contents_clob.getvalue()[0]
                    generated_id = file_id.getvalue()[0]
                    
                    # Write content in 32KB chunks to avoid PGA memory issues
                    chunk_size = 32767  # Oracle VARCHAR2 max size
                    file_contents = ach_file.file_contents
                    offset = 0
                    total_length = len(file_contents)
                    
                    while offset < total_length:
                        chunk = file_contents[offset:offset + chunk_size]
                        chunk_length = len(chunk)
                        cursor.execute(
                            "BEGIN DBMS_LOB.WRITEAPPEND(:clob, :amount, :buffer); END;",
                            {'clob': clob, 'amount': chunk_length, 'buffer': chunk}
                        )
                        offset += chunk_length
                    
                    conn.commit()
                    logger.info(f"Created ACH_FILES record {generated_id} with large CLOB ({file_contents_size} bytes) using DBMS_LOB")
                    return generated_id
                
                # For small CLOBs, use standard INSERT
                insert_sql = """
                INSERT INTO ACH_FILES (
                    ORIGINAL_FILENAME,
                    PROCESSING_STATUS,
                    FILE_CONTENTS,
                    CREATED_BY_USER,
                    CREATED_DATE,
                    CLIENT_ID,
                    CLIENT_NAME,
                    FILE_UPLOAD_FOLDER,
                    FILE_UPLOAD_FILENAME,
                    MEMO
                ) VALUES (
                    :original_filename,
                    :processing_status,
                    :file_contents,
                    :created_by_user,
                    CURRENT_TIMESTAMP,
                    :client_id,
                    :client_name,
                    :file_upload_folder,
                    :file_upload_filename,
                    :memo
                ) RETURNING FILE_ID INTO :file_id
                """
                
                # Execute insert
                file_id = cursor.var(int)
                cursor.execute(insert_sql, {
                    'original_filename': ach_file.original_filename,
                    'processing_status': ach_file.processing_status,
                    'file_contents': ach_file.file_contents,
                    'created_by_user': ach_file.created_by_user,
                    'client_id': ach_file.client_id,
                    'client_name': ach_file.client_name,
                    'file_upload_folder': ach_file.file_upload_folder,
                    'file_upload_filename': ach_file.file_upload_filename,
                    'memo': ach_file.memo,
                    'file_id': file_id
                })
                
                conn.commit()
                generated_id = file_id.getvalue()[0]
                
                logger.info(f"Created ACH_FILES record with ID: {generated_id}")
                return generated_id
                
        except Exception as e:
            logger.error(f"Failed to create ACH_FILES record: {e}")
            raise
    
    def get_ach_file(self, file_id: int) -> Optional[AchFileResponse]:
        """Get an ACH_FILES record by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                select_sql = """
                SELECT 
                    FILE_ID,
                    ORIGINAL_FILENAME,
                    PROCESSING_STATUS,
                    FILE_CONTENTS,
                    CREATED_BY_USER,
                    CREATED_DATE,
                    UPDATED_BY_USER,
                    UPDATED_DATE,
                    CLIENT_ID,
                    CLIENT_NAME,
                    FILE_UPLOAD_FOLDER,
                    FILE_UPLOAD_FILENAME,
                    MEMO
                FROM ACH_FILES 
                WHERE FILE_ID = :file_id
                """
                
                cursor.execute(select_sql, {'file_id': file_id})
                row = cursor.fetchone()
                
                if row:
                    # Handle CLOB data - convert LOB to string
                    # For large CLOBs, read in chunks to avoid memory issues
                    file_contents = row[3]
                    if file_contents:
                        if hasattr(file_contents, 'read'):
                            # It's a LOB object, check size first
                            try:
                                lob_size = file_contents.size()
                                # For very large CLOBs (>10MB), truncate or skip content to avoid memory issues
                                if lob_size > 10 * 1024 * 1024:  # 10MB
                                    # For very large files, return a placeholder message
                                    file_contents = f"[File content too large to display ({lob_size} bytes)]"
                                else:
                                    # Read the CLOB content
                                    file_contents = file_contents.read()
                            except Exception as e:
                                logger.warning(f"Error reading CLOB for FILE_ID {file_id}: {e}")
                                file_contents = "[Error reading file content]"
                        elif isinstance(file_contents, str):
                            # Already a string, use as-is
                            pass
                        else:
                            # Unknown type, convert to string
                            file_contents = str(file_contents) if file_contents else None
                    else:
                        file_contents = None
                    
                    return AchFileResponse(
                        file_id=row[0],
                        original_filename=row[1],
                        processing_status=row[2],
                        file_contents=file_contents,
                        created_by_user=row[4],
                        created_date=row[5],
                        updated_by_user=row[6],
                        updated_date=row[7],
                        client_id=row[8],
                        client_name=row[9],
                        file_upload_folder=row[10],
                        file_upload_filename=row[11],
                        memo=row[12]
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to get ACH_FILES record {file_id}: {e}")
            raise
    
    def get_ach_files(self, limit: int = 100, offset: int = 0) -> List[AchFileResponse]:
        """Get list of ACH_FILES records, excluding files starting with 'FEDACHOUT' or ending with '.pdf'."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                select_sql = """
                SELECT 
                    FILE_ID,
                    ORIGINAL_FILENAME,
                    PROCESSING_STATUS,
                    CREATED_BY_USER,
                    CREATED_DATE,
                    UPDATED_BY_USER,
                    UPDATED_DATE,
                    CLIENT_ID,
                    CLIENT_NAME,
                    FILE_UPLOAD_FOLDER,
                    FILE_UPLOAD_FILENAME,
                    MEMO
                FROM ACH_FILES 
                WHERE NOT (ORIGINAL_FILENAME LIKE 'FEDACHOUT%' OR ORIGINAL_FILENAME LIKE '%.pdf')
                ORDER BY CREATED_DATE DESC
                OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
                """
                
                cursor.execute(select_sql, {'limit': limit, 'offset': offset})
                rows = cursor.fetchall()
                
                files = []
                for row in rows:
                    # FILE_CONTENTS is excluded from list query to avoid CLOB reading issues
                    # Use get_ach_file(file_id) to retrieve individual file contents
                    files.append(AchFileResponse(
                        file_id=row[0],
                        original_filename=row[1],
                        processing_status=row[2],
                        file_contents=None,  # Excluded from list query
                        created_by_user=row[3],
                        created_date=row[4],
                        updated_by_user=row[5],
                        updated_date=row[6],
                        client_id=row[7],
                        client_name=row[8],
                        file_upload_folder=row[9],
                        file_upload_filename=row[10],
                        memo=row[11]
                    ))
                
                logger.info(f"Retrieved {len(files)} ACH_FILES records")
                return files
                
        except Exception as e:
            logger.error(f"Failed to get ACH_FILES records: {e}")
            raise
    
    def update_ach_file(self, file_id: int, ach_file: AchFileUpdate) -> bool:
        """Update an ACH_FILES record.
        
        For large CLOB updates (>1MB), uses DBMS_LOB to reduce PGA memory usage.
        This prevents ORA-04036 errors when updating large file contents.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if we need to update FILE_CONTENTS (large CLOB)
                # Use more conservative threshold (500KB) and check both string length and encoded size
                if ach_file.file_contents:
                    # Check both character length and byte size to be safe
                    char_length = len(ach_file.file_contents)
                    byte_size = len(ach_file.file_contents.encode('utf-8'))
                    file_contents_size = max(char_length, byte_size)
                else:
                    file_contents_size = 0
                # Lower threshold to 500KB to be more conservative and prevent edge cases
                use_lob_update = file_contents_size > 512 * 1024  # 500KB threshold
                
                # If updating large CLOB, use DBMS_LOB approach
                if ach_file.file_contents is not None and use_lob_update:
                    # First, update non-CLOB fields
                    update_fields = []
                    params = {'file_id': file_id}
                    
                    if ach_file.processing_status is not None:
                        update_fields.append("PROCESSING_STATUS = :processing_status")
                        params['processing_status'] = ach_file.processing_status
                    
                    if ach_file.updated_by_user is not None:
                        update_fields.append("UPDATED_BY_USER = :updated_by_user")
                        params['updated_by_user'] = ach_file.updated_by_user
                    
                    if ach_file.client_id is not None:
                        update_fields.append("CLIENT_ID = :client_id")
                        params['client_id'] = ach_file.client_id
                    
                    if ach_file.client_name is not None:
                        update_fields.append("CLIENT_NAME = :client_name")
                        params['client_name'] = ach_file.client_name
                    
                    if ach_file.file_upload_folder is not None:
                        update_fields.append("FILE_UPLOAD_FOLDER = :file_upload_folder")
                        params['file_upload_folder'] = ach_file.file_upload_folder
                    
                    if ach_file.file_upload_filename is not None:
                        update_fields.append("FILE_UPLOAD_FILENAME = :file_upload_filename")
                        params['file_upload_filename'] = ach_file.file_upload_filename
                    
                    if ach_file.memo is not None:
                        update_fields.append("MEMO = :memo")
                        params['memo'] = ach_file.memo
                    
                    if update_fields:
                        update_fields.append("UPDATED_DATE = CURRENT_TIMESTAMP")
                        update_sql = f"""
                        UPDATE ACH_FILES 
                        SET {', '.join(update_fields)}
                        WHERE FILE_ID = :file_id
                        """
                        cursor.execute(update_sql, params)
                    
                    # Now update CLOB using DBMS_LOB (chunked, memory-efficient)
                    # Get the CLOB locator and write in chunks to avoid PGA memory issues
                    get_lob_sql = """
                    SELECT FILE_CONTENTS 
                    FROM ACH_FILES
                    WHERE FILE_ID = :file_id
                    FOR UPDATE
                    """
                    cursor.execute(get_lob_sql, {'file_id': file_id})
                    row = cursor.fetchone()
                    if not row:
                        return False
                    
                    clob = row[0]
                    
                    # Truncate existing content
                    cursor.execute("BEGIN DBMS_LOB.TRUNCATE(:clob, 0); END;", {'clob': clob})
                    
                    # Write in 32KB chunks to avoid PGA memory issues
                    chunk_size = 32767  # Oracle VARCHAR2 max size
                    file_contents = ach_file.file_contents
                    offset = 0
                    total_length = len(file_contents)
                    
                    while offset < total_length:
                        chunk = file_contents[offset:offset + chunk_size]
                        chunk_length = len(chunk)
                        cursor.execute(
                            "BEGIN DBMS_LOB.WRITEAPPEND(:clob, :amount, :buffer); END;",
                            {'clob': clob, 'amount': chunk_length, 'buffer': chunk}
                        )
                        offset += chunk_length
                    
                    conn.commit()
                    logger.info(f"Updated ACH_FILES record {file_id} with large CLOB ({file_contents_size} bytes) using DBMS_LOB")
                    return True
                
                # For small CLOBs or no CLOB update, use standard UPDATE
                update_fields = []
                params = {'file_id': file_id}
                
                if ach_file.processing_status is not None:
                    update_fields.append("PROCESSING_STATUS = :processing_status")
                    params['processing_status'] = ach_file.processing_status
                
                if ach_file.file_contents is not None:
                    update_fields.append("FILE_CONTENTS = :file_contents")
                    params['file_contents'] = ach_file.file_contents
                
                if ach_file.updated_by_user is not None:
                    update_fields.append("UPDATED_BY_USER = :updated_by_user")
                    params['updated_by_user'] = ach_file.updated_by_user
                
                if ach_file.client_id is not None:
                    update_fields.append("CLIENT_ID = :client_id")
                    params['client_id'] = ach_file.client_id
                
                if ach_file.client_name is not None:
                    update_fields.append("CLIENT_NAME = :client_name")
                    params['client_name'] = ach_file.client_name
                
                if ach_file.file_upload_folder is not None:
                    update_fields.append("FILE_UPLOAD_FOLDER = :file_upload_folder")
                    params['file_upload_folder'] = ach_file.file_upload_folder
                
                if ach_file.file_upload_filename is not None:
                    update_fields.append("FILE_UPLOAD_FILENAME = :file_upload_filename")
                    params['file_upload_filename'] = ach_file.file_upload_filename
                
                if ach_file.memo is not None:
                    update_fields.append("MEMO = :memo")
                    params['memo'] = ach_file.memo
                
                if not update_fields:
                    return False  # No fields to update
                
                update_fields.append("UPDATED_DATE = CURRENT_TIMESTAMP")
                
                update_sql = f"""
                UPDATE ACH_FILES 
                SET {', '.join(update_fields)}
                WHERE FILE_ID = :file_id
                """
                
                cursor.execute(update_sql, params)
                conn.commit()
                
                rows_affected = cursor.rowcount
                logger.info(f"Updated ACH_FILES record {file_id}, rows affected: {rows_affected}")
                return rows_affected > 0
                
        except Exception as e:
            logger.error(f"Failed to update ACH_FILES record {file_id}: {e}")
            raise
    
    def update_ach_file_by_file_id(
        self, 
        file_id: int, 
        file_contents: str, 
        updated_by_user: str = "system-user",
        updated_date: Optional[datetime] = None
    ) -> bool:
        """Update ACH_FILES record by file_id with file_contents, updated_by_user, and updated_date.
        
        For large CLOB updates (>1MB), uses DBMS_LOB to reduce PGA memory usage.
        This prevents ORA-04036 errors when updating large file contents.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check file size to determine update method
                # Use more conservative threshold (500KB) and check both string length and encoded size
                char_length = len(file_contents)
                byte_size = len(file_contents.encode('utf-8'))
                file_contents_size = max(char_length, byte_size)
                # Lower threshold to 500KB to be more conservative and prevent edge cases
                use_lob_update = file_contents_size > 512 * 1024  # 500KB threshold
                
                if use_lob_update:
                    # Update non-CLOB fields first
                    if updated_date is not None:
                        update_sql = """
                        UPDATE ACH_FILES 
                        SET UPDATED_BY_USER = :updated_by_user,
                            UPDATED_DATE = :updated_date
                        WHERE FILE_ID = :file_id
                        """
                        cursor.execute(update_sql, {
                            'file_id': file_id,
                            'updated_by_user': updated_by_user,
                            'updated_date': updated_date
                        })
                    else:
                        update_sql = """
                        UPDATE ACH_FILES 
                        SET UPDATED_BY_USER = :updated_by_user,
                            UPDATED_DATE = CURRENT_TIMESTAMP
                        WHERE FILE_ID = :file_id
                        """
                        cursor.execute(update_sql, {
                            'file_id': file_id,
                            'updated_by_user': updated_by_user
                        })
                    
                    # Update CLOB using DBMS_LOB (chunked, memory-efficient)
                    # Get the CLOB locator and write in chunks to avoid PGA memory issues
                    get_lob_sql = """
                    SELECT FILE_CONTENTS 
                    FROM ACH_FILES
                    WHERE FILE_ID = :file_id
                    FOR UPDATE
                    """
                    cursor.execute(get_lob_sql, {'file_id': file_id})
                    row = cursor.fetchone()
                    if not row:
                        return False
                    
                    clob = row[0]
                    
                    # Truncate existing content
                    cursor.execute("BEGIN DBMS_LOB.TRUNCATE(:clob, 0); END;", {'clob': clob})
                    
                    # Write in 32KB chunks to avoid PGA memory issues
                    chunk_size = 32767  # Oracle VARCHAR2 max size
                    offset = 0
                    total_length = len(file_contents)
                    
                    while offset < total_length:
                        chunk = file_contents[offset:offset + chunk_size]
                        chunk_length = len(chunk)
                        cursor.execute(
                            "BEGIN DBMS_LOB.WRITEAPPEND(:clob, :amount, :buffer); END;",
                            {'clob': clob, 'amount': chunk_length, 'buffer': chunk}
                        )
                        offset += chunk_length
                    
                    conn.commit()
                    logger.info(f"Updated ACH_FILES record {file_id} with large CLOB ({file_contents_size} bytes) using DBMS_LOB")
                    return True
                
                # For small CLOBs, use standard UPDATE
                if updated_date is not None:
                    update_sql = """
                    UPDATE ACH_FILES 
                    SET FILE_CONTENTS = :file_contents,
                        UPDATED_BY_USER = :updated_by_user,
                        UPDATED_DATE = :updated_date
                    WHERE FILE_ID = :file_id
                    """
                    params = {
                        'file_id': file_id,
                        'file_contents': file_contents,
                        'updated_by_user': updated_by_user,
                        'updated_date': updated_date
                    }
                else:
                    update_sql = """
                    UPDATE ACH_FILES 
                    SET FILE_CONTENTS = :file_contents,
                        UPDATED_BY_USER = :updated_by_user,
                        UPDATED_DATE = CURRENT_TIMESTAMP
                    WHERE FILE_ID = :file_id
                    """
                    params = {
                        'file_id': file_id,
                        'file_contents': file_contents,
                        'updated_by_user': updated_by_user
                    }
                
                cursor.execute(update_sql, params)
                conn.commit()
                
                rows_affected = cursor.rowcount
                logger.info(f"Updated ACH_FILES record {file_id} by file_id, rows affected: {rows_affected}")
                return rows_affected > 0
                
        except Exception as e:
            logger.error(f"Failed to update ACH_FILES record {file_id} by file_id: {e}")
            raise
    
    def get_audit_ach_files_by_file_id(self, file_id: int) -> List[Dict[str, Any]]:
        """Get AUDIT_ACH_FILES records for a specific file_id."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                select_sql = """
                SELECT 
                    AUDIT_ID,
                    FILE_ID,
                    ORIGINAL_FILENAME,
                    PROCESSING_STATUS,
                    FILE_CONTENTS,
                    CREATED_BY_USER,
                    CREATED_DATE,
                    UPDATED_BY_USER,
                    UPDATED_DATE,
                    CLIENT_ID,
                    CLIENT_NAME,
                    FILE_UPLOAD_FOLDER,
                    FILE_UPLOAD_FILENAME,
                    MEMO
                FROM AUDIT_ACH_FILES 
                WHERE FILE_ID = :file_id
                ORDER BY AUDIT_ID DESC
                """
                
                cursor.execute(select_sql, {'file_id': file_id})
                rows = cursor.fetchall()
                
                audit_records = []
                for row in rows:
                    # Handle CLOB data - convert LOB to string
                    file_contents = row[4]
                    if hasattr(file_contents, 'read'):
                        file_contents = file_contents.read()
                    
                    audit_records.append({
                        'audit_id': row[0],
                        'file_id': row[1],
                        'original_filename': row[2],
                        'processing_status': row[3],
                        'file_contents': file_contents,
                        'created_by_user': row[5],
                        'created_date': row[6],
                        'updated_by_user': row[7],
                        'updated_date': row[8],
                        'client_id': row[9],
                        'client_name': row[10],
                        'file_upload_folder': row[11],
                        'file_upload_filename': row[12],
                        'memo': row[13]
                    })
                
                logger.info(f"Retrieved {len(audit_records)} AUDIT_ACH_FILES records for FILE_ID: {file_id}")
                return audit_records
                
        except Exception as e:
            logger.error(f"Failed to get AUDIT_ACH_FILES records for FILE_ID {file_id}: {e}")
            raise
    
    def delete_ach_file(self, file_id: int) -> bool:
        """Delete an ACH_FILES record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                delete_sql = "DELETE FROM ACH_FILES WHERE FILE_ID = :file_id"
                cursor.execute(delete_sql, {'file_id': file_id})
                conn.commit()
                
                rows_affected = cursor.rowcount
                logger.info(f"Deleted ACH_FILES record {file_id}, rows affected: {rows_affected}")
                return rows_affected > 0
                
        except Exception as e:
            logger.error(f"Failed to delete ACH_FILES record {file_id}: {e}")
            raise
    
    def get_ach_files_count(self) -> int:
        """Get total count of ACH_FILES records, excluding files starting with 'FEDACHOUT' or ending with '.pdf'."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                count_sql = """
                SELECT COUNT(*) 
                FROM ACH_FILES 
                WHERE NOT (ORIGINAL_FILENAME LIKE 'FEDACHOUT%' OR ORIGINAL_FILENAME LIKE '%.pdf')
                """
                cursor.execute(count_sql)
                count = cursor.fetchone()[0]
                
                return count
                
        except Exception as e:
            logger.error(f"Failed to get ACH_FILES count: {e}")
            raise
    
    def get_active_clients(self) -> List[Dict[str, Any]]:
        """Get active clients from ACH_CLIENTS table where CLIENT_STATUS = 'Active'."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                select_sql = f"""
                SELECT 
                    CLIENT_ID,
                    CLIENT_NAME
                FROM {self.config.db_schema}.ACH_CLIENTS
                WHERE CLIENT_STATUS = 'Active'
                ORDER BY CLIENT_NAME
                """
                
                cursor.execute(select_sql)
                rows = cursor.fetchall()
                
                clients = []
                for row in rows:
                    clients.append({
                        'client_id': str(row[0]),
                        'client_name': row[1]
                    })
                
                logger.info(f"Retrieved {len(clients)} active clients from ACH_CLIENTS")
                return clients
                
        except Exception as e:
            logger.error(f"Failed to get active clients: {e}")
            raise
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with email and plain password using bcrypt verification.
        
        This method:
        1. Retrieves the user record from API_USERS by email
        2. Checks if user is active
        3. Uses bcrypt.verify() (via passlib) to verify the plain password
           against the stored hash
        4. Returns authentication status and admin flag
        
        Args:
            email: User email address
            password: Plain text password to verify
            
        Returns:
            Dictionary with:
            - authenticated: bool - True if password matches stored hash
            - is_admin: bool - True if user is admin (only when authenticated=True)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get user record with stored password hash
                select_sql = """
                SELECT PASSWORD_HASH, IS_ADMIN, IS_ACTIVE
                FROM API_USERS
                WHERE UPPER(EMAIL) = UPPER(:email)
                """
                
                cursor.execute(select_sql, {'email': email})
                result = cursor.fetchone()
                
                # Check if user exists
                if not result:
                    logger.warning(f"Authentication failed: User not found for email: {email}")
                    return {
                        'authenticated': False,
                        'is_admin': False
                    }
                
                stored_hash, is_admin, is_active = result
                
                # Check if user is active
                if not is_active:
                    logger.warning(f"Authentication failed: User is inactive: {email}")
                    return {
                        'authenticated': False,
                        'is_admin': False
                    }
                
                # Use bcrypt to verify password against stored hash
                # This is the standard, secure way to validate passwords
                # Use bcrypt directly to avoid passlib compatibility issues
                try:
                    # Encode password to bytes for bcrypt
                    password_bytes = password.encode('utf-8')
                    hash_bytes = stored_hash.encode('utf-8')
                    password_matches = bcrypt.checkpw(password_bytes, hash_bytes)
                except Exception as verify_error:
                    logger.error(f"Bcrypt verification error: {verify_error}")
                    password_matches = False
                
                if password_matches:
                    logger.info(f"Authentication successful for: {email} (IS_ADMIN: {is_admin})")
                    return {
                        'authenticated': True,
                        'is_admin': bool(is_admin) if is_admin is not None else False
                    }
                else:
                    logger.warning(f"Authentication failed: Invalid password for email: {email}")
                    return {
                        'authenticated': False,
                        'is_admin': False
                    }
                
        except Exception as e:
            logger.error(f"Failed to authenticate user {email}: {e}")
            return {
                'authenticated': False,
                'is_admin': False
            }
    
    def insert_ach_file_header(self, file_id: int, record: AchFileHeaderCreate) -> int:
        """Insert ACH_FILE_HEADER record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ACH_FILE_HEADER (
                        FILE_HEADER_ID, FILE_ID, RECORD_TYPE_CODE, PRIORITY_CODE,
                        IMMEDIATE_DESTINATION, IMMEDIATE_ORIGIN, FILE_CREATION_DATE,
                        FILE_CREATION_TIME, FILE_ID_MODIFIER, RECORD_SIZE,
                        BLOCKING_FACTOR, FORMAT_CODE, IMMEDIATE_DEST_NAME,
                        IMMEDIATE_ORIGIN_NAME, REFERENCE_CODE, RAW_RECORD
                    ) VALUES (
                        SEQ_FILE_HEADER.NEXTVAL, :file_id, :record_type_code, :priority_code,
                        :immediate_destination, :immediate_origin, :file_creation_date,
                        :file_creation_time, :file_id_modifier, :record_size,
                        :blocking_factor, :format_code, :immediate_dest_name,
                        :immediate_origin_name, :reference_code, :raw_record
                    )
                """, {
                    'file_id': file_id,
                    'record_type_code': record.record_type_code,
                    'priority_code': record.priority_code,
                    'immediate_destination': record.immediate_destination,
                    'immediate_origin': record.immediate_origin,
                    'file_creation_date': record.file_creation_date,
                    'file_creation_time': record.file_creation_time,
                    'file_id_modifier': record.file_id_modifier,
                    'record_size': record.record_size,
                    'blocking_factor': record.blocking_factor,
                    'format_code': record.format_code,
                    'immediate_dest_name': record.immediate_dest_name,
                    'immediate_origin_name': record.immediate_origin_name,
                    'reference_code': record.reference_code,
                    'raw_record': record.raw_record
                })
                conn.commit()
                cursor.execute("SELECT SEQ_FILE_HEADER.CURRVAL FROM DUAL")
                header_id = cursor.fetchone()[0]
                logger.info(f"Inserted ACH_FILE_HEADER record {header_id} for file_id {file_id}")
                return header_id
        except Exception as e:
            logger.error(f"Failed to insert ACH_FILE_HEADER: {e}")
            raise
    
    def insert_ach_batch_header(self, file_id: int, record: AchBatchHeaderCreate) -> int:
        """Insert ACH_BATCH_HEADER record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ACH_BATCH_HEADER (
                        BATCH_HEADER_ID, FILE_ID, BATCH_NUMBER, RECORD_TYPE_CODE,
                        SERVICE_CLASS_CODE, COMPANY_NAME, COMPANY_DISCRETIONARY_DATA,
                        COMPANY_IDENTIFICATION, STANDARD_ENTRY_CLASS_CODE,
                        COMPANY_ENTRY_DESCRIPTION, COMPANY_DESCRIPTIVE_DATE,
                        EFFECTIVE_ENTRY_DATE, SETTLEMENT_DATE, ORIGINATOR_STATUS_CODE,
                        ORIGINATING_DFI_ID, RAW_RECORD
                    ) VALUES (
                        SEQ_BATCH_HEADER.NEXTVAL, :file_id, :batch_number, :record_type_code,
                        :service_class_code, :company_name, :company_discretionary_data,
                        :company_identification, :standard_entry_class_code,
                        :company_entry_description, :company_descriptive_date,
                        :effective_entry_date, :settlement_date, :originator_status_code,
                        :originating_dfi_id, :raw_record
                    )
                """, {
                    'file_id': file_id,
                    'batch_number': record.batch_number,
                    'record_type_code': record.record_type_code,
                    'service_class_code': record.service_class_code,
                    'company_name': record.company_name,
                    'company_discretionary_data': record.company_discretionary_data,
                    'company_identification': record.company_identification,
                    'standard_entry_class_code': record.standard_entry_class_code,
                    'company_entry_description': record.company_entry_description,
                    'company_descriptive_date': record.company_descriptive_date,
                    'effective_entry_date': record.effective_entry_date,
                    'settlement_date': record.settlement_date,
                    'originator_status_code': record.originator_status_code,
                    'originating_dfi_id': record.originating_dfi_id,
                    'raw_record': record.raw_record
                })
                conn.commit()
                cursor.execute("SELECT SEQ_BATCH_HEADER.CURRVAL FROM DUAL")
                header_id = cursor.fetchone()[0]
                logger.info(f"Inserted ACH_BATCH_HEADER record {header_id} for file_id {file_id}, batch {record.batch_number}")
                return header_id
        except Exception as e:
            logger.error(f"Failed to insert ACH_BATCH_HEADER: {e}")
            raise
    
    def insert_ach_entry_detail(self, file_id: int, record: AchEntryDetailCreate) -> int:
        """Insert ACH_ENTRY_DETAIL record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ACH_ENTRY_DETAIL (
                        ENTRY_DETAIL_ID, FILE_ID, BATCH_NUMBER, RECORD_TYPE_CODE,
                        TRANSACTION_CODE, RECEIVING_DFI_ID, CHECK_DIGIT,
                        DFI_ACCOUNT_NUMBER, AMOUNT, AMOUNT_DECIMAL,
                        INDIVIDUAL_ID_NUMBER, INDIVIDUAL_NAME, DISCRETIONARY_DATA,
                        ADDENDA_RECORD_INDICATOR, TRACE_NUMBER, TRACE_SEQUENCE_NUMBER,
                        RAW_RECORD
                    ) VALUES (
                        SEQ_ENTRY_DETAIL.NEXTVAL, :file_id, :batch_number, :record_type_code,
                        :transaction_code, :receiving_dfi_id, :check_digit,
                        :dfi_account_number, :amount, :amount_decimal,
                        :individual_id_number, :individual_name, :discretionary_data,
                        :addenda_record_indicator, :trace_number, :trace_sequence_number,
                        :raw_record
                    )
                """, {
                    'file_id': file_id,
                    'batch_number': record.batch_number,
                    'record_type_code': record.record_type_code,
                    'transaction_code': record.transaction_code,
                    'receiving_dfi_id': record.receiving_dfi_id,
                    'check_digit': record.check_digit,
                    'dfi_account_number': record.dfi_account_number,
                    'amount': record.amount,
                    'amount_decimal': record.amount_decimal,
                    'individual_id_number': record.individual_id_number,
                    'individual_name': record.individual_name,
                    'discretionary_data': record.discretionary_data,
                    'addenda_record_indicator': record.addenda_record_indicator,
                    'trace_number': record.trace_number,
                    'trace_sequence_number': record.trace_sequence_number,
                    'raw_record': record.raw_record
                })
                conn.commit()
                cursor.execute("SELECT SEQ_ENTRY_DETAIL.CURRVAL FROM DUAL")
                entry_id = cursor.fetchone()[0]
                logger.info(f"Inserted ACH_ENTRY_DETAIL record {entry_id} for file_id {file_id}, batch {record.batch_number}")
                return entry_id
        except Exception as e:
            logger.error(f"Failed to insert ACH_ENTRY_DETAIL: {e}")
            raise
    
    def insert_ach_addenda(self, file_id: int, record: AchAddendaCreate, entry_detail_id: Optional[int] = None) -> int:
        """Insert ACH_ADDENDA record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ACH_ADDENDA (
                        ADDENDA_ID, FILE_ID, ENTRY_DETAIL_ID, BATCH_NUMBER,
                        RECORD_TYPE_CODE, ADDENDA_TYPE_CODE, PAYMENT_RELATED_INFO,
                        ADDENDA_SEQUENCE_NUMBER, ENTRY_DETAIL_SEQUENCE_NUM, RAW_RECORD
                    ) VALUES (
                        SEQ_ADDENDA.NEXTVAL, :file_id, :entry_detail_id, :batch_number,
                        :record_type_code, :addenda_type_code, :payment_related_info,
                        :addenda_sequence_number, :entry_detail_sequence_num, :raw_record
                    )
                """, {
                    'file_id': file_id,
                    'entry_detail_id': entry_detail_id,
                    'batch_number': record.batch_number,
                    'record_type_code': record.record_type_code,
                    'addenda_type_code': record.addenda_type_code,
                    'payment_related_info': record.payment_related_info,
                    'addenda_sequence_number': record.addenda_sequence_number,
                    'entry_detail_sequence_num': record.entry_detail_sequence_num,
                    'raw_record': record.raw_record
                })
                conn.commit()
                cursor.execute("SELECT SEQ_ADDENDA.CURRVAL FROM DUAL")
                addenda_id = cursor.fetchone()[0]
                logger.info(f"Inserted ACH_ADDENDA record {addenda_id} for file_id {file_id}, batch {record.batch_number}")
                return addenda_id
        except Exception as e:
            logger.error(f"Failed to insert ACH_ADDENDA: {e}")
            raise
    
    def insert_ach_batch_control(self, file_id: int, record: AchBatchControlCreate) -> int:
        """Insert ACH_BATCH_CONTROL record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ACH_BATCH_CONTROL (
                        BATCH_CONTROL_ID, FILE_ID, BATCH_NUMBER, RECORD_TYPE_CODE,
                        SERVICE_CLASS_CODE, ENTRY_ADDENDA_COUNT, ENTRY_HASH,
                        TOTAL_DEBIT_AMOUNT, TOTAL_DEBIT_AMOUNT_DECIMAL,
                        TOTAL_CREDIT_AMOUNT, TOTAL_CREDIT_AMOUNT_DECIMAL,
                        COMPANY_IDENTIFICATION, MESSAGE_AUTH_CODE, RESERVED,
                        ORIGINATING_DFI_ID, RAW_RECORD
                    ) VALUES (
                        SEQ_BATCH_CONTROL.NEXTVAL, :file_id, :batch_number, :record_type_code,
                        :service_class_code, :entry_addenda_count, :entry_hash,
                        :total_debit_amount, :total_debit_amount_decimal,
                        :total_credit_amount, :total_credit_amount_decimal,
                        :company_identification, :message_auth_code, :reserved,
                        :originating_dfi_id, :raw_record
                    )
                """, {
                    'file_id': file_id,
                    'batch_number': record.batch_number,
                    'record_type_code': record.record_type_code,
                    'service_class_code': record.service_class_code,
                    'entry_addenda_count': record.entry_addenda_count,
                    'entry_hash': record.entry_hash,
                    'total_debit_amount': record.total_debit_amount,
                    'total_debit_amount_decimal': record.total_debit_amount_decimal,
                    'total_credit_amount': record.total_credit_amount,
                    'total_credit_amount_decimal': record.total_credit_amount_decimal,
                    'company_identification': record.company_identification,
                    'message_auth_code': record.message_auth_code,
                    'reserved': record.reserved,
                    'originating_dfi_id': record.originating_dfi_id,
                    'raw_record': record.raw_record
                })
                conn.commit()
                cursor.execute("SELECT SEQ_BATCH_CONTROL.CURRVAL FROM DUAL")
                control_id = cursor.fetchone()[0]
                logger.info(f"Inserted ACH_BATCH_CONTROL record {control_id} for file_id {file_id}, batch {record.batch_number}")
                return control_id
        except Exception as e:
            logger.error(f"Failed to insert ACH_BATCH_CONTROL: {e}")
            raise
    
    def insert_ach_file_control(self, file_id: int, record: AchFileControlCreate) -> int:
        """Insert ACH_FILE_CONTROL record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ACH_FILE_CONTROL (
                        FILE_CONTROL_ID, FILE_ID, RECORD_TYPE_CODE, BATCH_COUNT,
                        BLOCK_COUNT, ENTRY_ADDENDA_COUNT, ENTRY_HASH,
                        TOTAL_DEBIT_AMOUNT, TOTAL_DEBIT_AMOUNT_DECIMAL,
                        TOTAL_CREDIT_AMOUNT, TOTAL_CREDIT_AMOUNT_DECIMAL,
                        RESERVED, RAW_RECORD
                    ) VALUES (
                        SEQ_FILE_CONTROL.NEXTVAL, :file_id, :record_type_code, :batch_count,
                        :block_count, :entry_addenda_count, :entry_hash,
                        :total_debit_amount, :total_debit_amount_decimal,
                        :total_credit_amount, :total_credit_amount_decimal,
                        :reserved, :raw_record
                    )
                """, {
                    'file_id': file_id,
                    'record_type_code': record.record_type_code,
                    'batch_count': record.batch_count,
                    'block_count': record.block_count,
                    'entry_addenda_count': record.entry_addenda_count,
                    'entry_hash': record.entry_hash,
                    'total_debit_amount': record.total_debit_amount,
                    'total_debit_amount_decimal': record.total_debit_amount_decimal,
                    'total_credit_amount': record.total_credit_amount,
                    'total_credit_amount_decimal': record.total_credit_amount_decimal,
                    'reserved': record.reserved,
                    'raw_record': record.raw_record
                })
                conn.commit()
                cursor.execute("SELECT SEQ_FILE_CONTROL.CURRVAL FROM DUAL")
                control_id = cursor.fetchone()[0]
                logger.info(f"Inserted ACH_FILE_CONTROL record {control_id} for file_id {file_id}")
                return control_id
        except Exception as e:
            logger.error(f"Failed to insert ACH_FILE_CONTROL: {e}")
            raise
    
    def parse_and_insert_ach_records(self, file_id: int, file_contents: str) -> Dict[str, int]:
        """Parse ACH file contents and insert records into appropriate tables.
        
        Returns a dictionary with counts of inserted records:
        {
            'file_headers': count,
            'batch_headers': count,
            'entry_details': count,
            'addendas': count,
            'batch_controls': count,
            'file_controls': count
        }
        """
        from .ach_record_parser import ACHRecordParser
        
        try:
            # Parse file content
            parsed_records = ACHRecordParser.parse_file_content(file_contents)
            
            counts = {
                'file_headers': 0,
                'batch_headers': 0,
                'entry_details': 0,
                'addendas': 0,
                'batch_controls': 0,
                'file_controls': 0
            }
            
            # Track entry details for linking addendas
            entry_detail_map = {}  # Maps (batch_number, trace_sequence) -> entry_detail_id
            
            # Insert file headers
            for record in parsed_records['file_headers']:
                record.file_id = file_id
                self.insert_ach_file_header(file_id, record)
                counts['file_headers'] += 1
            
            # Insert batch headers
            for record in parsed_records['batch_headers']:
                record.file_id = file_id
                self.insert_ach_batch_header(file_id, record)
                counts['batch_headers'] += 1
            
            # Insert entry details
            for record in parsed_records['entry_details']:
                record.file_id = file_id
                entry_id = self.insert_ach_entry_detail(file_id, record)
                counts['entry_details'] += 1
                
                # Store entry detail ID for linking addendas
                if record.trace_sequence_number:
                    key = (record.batch_number, record.trace_sequence_number)
                    entry_detail_map[key] = entry_id
            
            # Insert addendas (try to link to entry details)
            for record in parsed_records['addendas']:
                record.file_id = file_id
                entry_detail_id = None
                
                # Try to find matching entry detail
                if record.entry_detail_sequence_num:
                    key = (record.batch_number, record.entry_detail_sequence_num)
                    entry_detail_id = entry_detail_map.get(key)
                
                self.insert_ach_addenda(file_id, record, entry_detail_id)
                counts['addendas'] += 1
            
            # Insert batch controls
            for record in parsed_records['batch_controls']:
                record.file_id = file_id
                self.insert_ach_batch_control(file_id, record)
                counts['batch_controls'] += 1
            
            # Insert file controls
            for record in parsed_records['file_controls']:
                record.file_id = file_id
                self.insert_ach_file_control(file_id, record)
                counts['file_controls'] += 1
            
            logger.info(f"Parsed and inserted ACH records for file_id {file_id}: {counts}")
            return counts
            
        except Exception as e:
            logger.error(f"Failed to parse and insert ACH records for file_id {file_id}: {e}")
            raise
    
    def get_ach_data_for_core_post_sp_approved(
        self,
        file_id: Optional[int] = None,
        client_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get ACH data for Core Post Stored Procedure (approved files only).
        
        Returns entry detail records with all related data needed for the stored procedure.
        
        Args:
            file_id: Optional filter by specific file_id
            client_id: Optional filter by specific client_id
            limit: Optional limit number of records
            offset: Optional offset for pagination
            
        Returns:
            List of dictionaries containing ACH data for each entry detail record
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause dynamically
                where_conditions = [
                    "ed.RECORD_TYPE_CODE = '6'",
                    "af.PROCESSING_STATUS = 'APPROVED'"
                ]
                params = {}
                
                if file_id is not None:
                    where_conditions.append("ed.FILE_ID = :file_id")
                    params['file_id'] = file_id
                
                if client_id is not None:
                    where_conditions.append("af.CLIENT_ID = :client_id")
                    params['client_id'] = client_id
                
                where_clause = " AND ".join(where_conditions)
                
                # Build query with optional pagination
                query = f"""
                    SELECT
                        -- Trace Sequence Number (GN_SECUENCIACONVENIO)
                        ed.TRACE_SEQUENCE_NUMBER AS trace_sequence_number,
                        
                        -- Client ID (GN_CODIGOCLIENTE)
                        af.CLIENT_ID AS client_id,
                        
                        -- Origin Agency (GN_AGENCIACTAORIGEN)
                        SUBSTR(bh.ORIGINATING_DFI_ID, 1, 3) AS origin_agency,
                        
                        -- Origin Sub-account (GN_SUBCTAORIGEN)
                        0 AS origin_sub_account,
                        
                        -- ACH Class (GV_APLCTAORIGEN)
                        bh.STANDARD_ENTRY_CLASS_CODE AS ach_class,
                        
                        -- Origin Account (GN_CTAORIGEN)
                        ed.DFI_ACCOUNT_NUMBER AS origin_account,
                        
                        -- Company ID (GN_EMPCTAORIGEN)
                        bh.COMPANY_IDENTIFICATION AS company_id,
                        
                        -- Company Entry Description
                        bh.COMPANY_ENTRY_DESCRIPTION AS company_entry_description,
                        
                        -- Receiver Routing/ABA (GN_ABABCORECIBIDOR)
                        ed.RECEIVING_DFI_ID || ed.CHECK_DIGIT AS receiver_routing_aba,
                        
                        -- Receiver Account (GV_CTABCORECIBIDOR)
                        ed.DFI_ACCOUNT_NUMBER AS receiver_account,
                        
                        -- Transaction Code (GN_PRODBCORECIBIDOR)
                        ed.TRANSACTION_CODE AS transaction_code,
                        
                        -- Company Name (GV_CUENTAINSTITUCION)
                        bh.COMPANY_NAME AS company_name,
                        
                        -- Receiver ID (GV_IDRECIBIDOR)
                        ed.INDIVIDUAL_ID_NUMBER AS receiver_id,
                        
                        -- Receiver Name (GV_NOMBRERECIBIDOR)
                        ed.INDIVIDUAL_NAME AS receiver_name,
                        
                        -- Reference (GV_REFERENCIA)
                        fh.REFERENCE_CODE AS reference_code,
                        
                        -- Payment Description (GV_DESCPAGO)
                        bh.COMPANY_ENTRY_DESCRIPTION AS payment_description,
                        
                        -- Amount (GN_MONTOOPERACION)
                        ed.AMOUNT_DECIMAL AS amount,
                        
                        -- Additional fields for filtering/identification
                        ed.ENTRY_DETAIL_ID,
                        ed.FILE_ID,
                        ed.BATCH_NUMBER,
                        af.ORIGINAL_FILENAME
                    FROM
                        ACH_ENTRY_DETAIL ed
                        INNER JOIN ACH_FILES af ON ed.FILE_ID = af.FILE_ID
                        INNER JOIN ACH_BATCH_HEADER bh 
                            ON ed.FILE_ID = bh.FILE_ID 
                            AND ed.BATCH_NUMBER = bh.BATCH_NUMBER
                        INNER JOIN ACH_FILE_HEADER fh ON ed.FILE_ID = fh.FILE_ID
                    WHERE
                        {where_clause}
                    ORDER BY
                        ed.FILE_ID, ed.BATCH_NUMBER, ed.ENTRY_DETAIL_ID
                """
                
                # Add pagination if specified
                if limit is not None:
                    if offset is not None:
                        query = f"""
                            SELECT * FROM (
                                SELECT a.*, ROWNUM rnum FROM (
                                    {query}
                                ) a WHERE ROWNUM <= :limit_offset
                            ) WHERE rnum > :offset
                        """
                        params['limit_offset'] = offset + limit
                        params['offset'] = offset
                    else:
                        query = f"""
                            SELECT * FROM (
                                {query}
                            ) WHERE ROWNUM <= :limit
                        """
                        params['limit'] = limit
                
                cursor.execute(query, params)
                
                # Fetch all results
                columns = [desc[0].lower() for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    results.append(record)
                
                logger.info(f"Retrieved {len(results)} ACH records for Core Post SP (approved files)")
                return results
                
        except Exception as e:
            logger.error(f"Failed to get ACH data for Core Post SP: {e}")
            raise
    
    # ==================== FI_HOLIDAYS CRUD Operations ====================
    
    def create_fi_holiday(self, holiday: FiHolidayCreate) -> int:
        """Create a new FI_HOLIDAYS record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                insert_sql = f"""
                INSERT INTO {self.config.db_schema}.FI_HOLIDAYS (
                    HOLIDAY_DATE,
                    HOLIDAY_NAME,
                    CREATED_BY_USER,
                    CREATED_DATE
                ) VALUES (
                    :holiday_date,
                    :holiday_name,
                    :created_by_user,
                    CURRENT_TIMESTAMP
                ) RETURNING HOLIDAY_ID INTO :holiday_id
                """
                
                holiday_id = cursor.var(int)
                cursor.execute(insert_sql, {
                    'holiday_date': holiday.holiday_date,
                    'holiday_name': holiday.holiday_name,
                    'created_by_user': holiday.created_by_user,
                    'holiday_id': holiday_id
                })
                
                conn.commit()
                generated_id = holiday_id.getvalue()[0]
                
                logger.info(f"Created FI_HOLIDAYS record with ID: {generated_id}")
                return generated_id
                
        except Exception as e:
            logger.error(f"Failed to create FI_HOLIDAYS record: {e}")
            raise
    
    def get_fi_holiday(self, holiday_id: int) -> Optional[FiHolidayResponse]:
        """Get a FI_HOLIDAYS record by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                select_sql = f"""
                SELECT 
                    HOLIDAY_ID,
                    HOLIDAY_DATE,
                    HOLIDAY_NAME,
                    CREATED_BY_USER,
                    CREATED_DATE,
                    UPDATED_BY_USER,
                    UPDATED_DATE
                FROM {self.config.db_schema}.FI_HOLIDAYS 
                WHERE HOLIDAY_ID = :holiday_id
                """
                
                cursor.execute(select_sql, {'holiday_id': holiday_id})
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return FiHolidayResponse(
                    holiday_id=row[0],
                    holiday_date=row[1],
                    holiday_name=row[2],
                    is_active=None,  # Column doesn't exist in table
                    created_by_user=row[3],
                    created_date=row[4],
                    updated_by_user=row[5],
                    updated_date=row[6]
                )
                
        except Exception as e:
            logger.error(f"Failed to get FI_HOLIDAYS record {holiday_id}: {e}")
            raise
    
    def get_fi_holidays(
        self,
        limit: int = 100,
        offset: int = 0,
        is_active: Optional[int] = None,
        year: Optional[int] = None
    ) -> List[FiHolidayResponse]:
        """Get list of FI_HOLIDAYS records with optional filtering."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause dynamically
                where_conditions = []
                params = {}
                
                # Note: IS_ACTIVE column doesn't exist in FI_HOLIDAYS table, so we skip that filter
                # if is_active is not None:
                #     where_conditions.append("IS_ACTIVE = :is_active")
                #     params['is_active'] = is_active
                
                if year is not None:
                    where_conditions.append("EXTRACT(YEAR FROM HOLIDAY_DATE) = :year")
                    params['year'] = year
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                select_sql = f"""
                SELECT 
                    HOLIDAY_ID,
                    HOLIDAY_DATE,
                    HOLIDAY_NAME,
                    CREATED_BY_USER,
                    CREATED_DATE,
                    UPDATED_BY_USER,
                    UPDATED_DATE
                FROM {self.config.db_schema}.FI_HOLIDAYS 
                WHERE {where_clause}
                ORDER BY HOLIDAY_DATE
                OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
                """
                
                params['offset'] = offset
                params['limit'] = limit
                
                cursor.execute(select_sql, params)
                rows = cursor.fetchall()
                
                holidays = []
                for row in rows:
                    holidays.append(FiHolidayResponse(
                        holiday_id=row[0],
                        holiday_date=row[1],
                        holiday_name=row[2],
                        is_active=None,  # Column doesn't exist in table
                        created_by_user=row[3],
                        created_date=row[4],
                        updated_by_user=row[5],
                        updated_date=row[6]
                    ))
                
                logger.info(f"Retrieved {len(holidays)} FI_HOLIDAYS records")
                return holidays
                
        except Exception as e:
            logger.error(f"Failed to get FI_HOLIDAYS records: {e}")
            raise
    
    def get_fi_holidays_count(
        self,
        is_active: Optional[int] = None,
        year: Optional[int] = None
    ) -> int:
        """Get total count of FI_HOLIDAYS records with optional filtering."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause dynamically
                where_conditions = []
                params = {}
                
                # Note: IS_ACTIVE column doesn't exist in FI_HOLIDAYS table, so we skip that filter
                # if is_active is not None:
                #     where_conditions.append("IS_ACTIVE = :is_active")
                #     params['is_active'] = is_active
                
                if year is not None:
                    where_conditions.append("EXTRACT(YEAR FROM HOLIDAY_DATE) = :year")
                    params['year'] = year
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                count_sql = f"""
                SELECT COUNT(*) 
                FROM {self.config.db_schema}.FI_HOLIDAYS 
                WHERE {where_clause}
                """
                
                cursor.execute(count_sql, params)
                count = cursor.fetchone()[0]
                
                return count
                
        except Exception as e:
            logger.error(f"Failed to get FI_HOLIDAYS count: {e}")
            raise
    
    def update_fi_holiday(self, holiday_id: int, holiday: FiHolidayUpdate) -> bool:
        """Update a FI_HOLIDAYS record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build update fields dynamically
                update_fields = []
                params = {'holiday_id': holiday_id}
                
                if holiday.holiday_date is not None:
                    update_fields.append("HOLIDAY_DATE = :holiday_date")
                    params['holiday_date'] = holiday.holiday_date
                
                if holiday.holiday_name is not None:
                    update_fields.append("HOLIDAY_NAME = :holiday_name")
                    params['holiday_name'] = holiday.holiday_name
                
                # Note: IS_ACTIVE column doesn't exist in FI_HOLIDAYS table
                # if holiday.is_active is not None:
                #     update_fields.append("IS_ACTIVE = :is_active")
                #     params['is_active'] = holiday.is_active
                
                if holiday.updated_by_user is not None:
                    update_fields.append("UPDATED_BY_USER = :updated_by_user")
                    params['updated_by_user'] = holiday.updated_by_user
                
                if not update_fields:
                    return False  # No fields to update
                
                update_fields.append("UPDATED_DATE = CURRENT_TIMESTAMP")
                
                update_sql = f"""
                UPDATE {self.config.db_schema}.FI_HOLIDAYS 
                SET {', '.join(update_fields)}
                WHERE HOLIDAY_ID = :holiday_id
                """
                
                cursor.execute(update_sql, params)
                conn.commit()
                
                rows_affected = cursor.rowcount
                logger.info(f"Updated FI_HOLIDAYS record {holiday_id}, rows affected: {rows_affected}")
                return rows_affected > 0
                
        except Exception as e:
            logger.error(f"Failed to update FI_HOLIDAYS record {holiday_id}: {e}")
            raise
    
    def delete_fi_holiday(self, holiday_id: int) -> bool:
        """Delete a FI_HOLIDAYS record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                delete_sql = f"DELETE FROM {self.config.db_schema}.FI_HOLIDAYS WHERE HOLIDAY_ID = :holiday_id"
                cursor.execute(delete_sql, {'holiday_id': holiday_id})
                conn.commit()
                
                rows_affected = cursor.rowcount
                logger.info(f"Deleted FI_HOLIDAYS record {holiday_id}, rows affected: {rows_affected}")
                return rows_affected > 0
                
        except Exception as e:
            logger.error(f"Failed to delete FI_HOLIDAYS record {holiday_id}: {e}")
            raise
    
    # ==================== ACH_ACCOUNT_NUMBER_SWAPS CRUD Operations ====================
    
    def create_ach_account_swap(self, swap: AchAccountSwapCreate) -> int:
        """Create a new ACH_ACCOUNT_NUMBER_SWAPS record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                insert_sql = f"""
                INSERT INTO {self.config.db_schema}.ACH_ACCOUNT_NUMBER_SWAPS (
                    ORIGINAL_DFI_ACCOUNT_NUMBER,
                    SWAP_ACCOUNT_NUMBER,
                    SWAP_MEMO,
                    CREATED_BY_USER,
                    CREATED_DATE
                ) VALUES (
                    :original_dfi_account_number,
                    :swap_account_number,
                    :swap_memo,
                    :created_by_user,
                    CURRENT_TIMESTAMP
                ) RETURNING SWAP_ID INTO :swap_id
                """
                
                swap_id = cursor.var(int)
                cursor.execute(insert_sql, {
                    'original_dfi_account_number': swap.original_dfi_account_number,
                    'swap_account_number': swap.swap_account_number,
                    'swap_memo': swap.swap_memo,
                    'created_by_user': swap.created_by_user,
                    'swap_id': swap_id
                })
                
                conn.commit()
                generated_id = swap_id.getvalue()[0]
                
                logger.info(f"Created ACH_ACCOUNT_NUMBER_SWAPS record with ID: {generated_id}")
                return generated_id
                
        except Exception as e:
            logger.error(f"Failed to create ACH_ACCOUNT_NUMBER_SWAPS record: {e}")
            raise
    
    def get_ach_account_swap(self, swap_id: int) -> Optional[AchAccountSwapResponse]:
        """Get a ACH_ACCOUNT_NUMBER_SWAPS record by SWAP_ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                select_sql = f"""
                SELECT 
                    SWAP_ID,
                    ORIGINAL_DFI_ACCOUNT_NUMBER,
                    SWAP_ACCOUNT_NUMBER,
                    SWAP_MEMO,
                    CREATED_BY_USER,
                    CREATED_DATE,
                    UPDATED_BY_USER,
                    UPDATED_DATE
                FROM {self.config.db_schema}.ACH_ACCOUNT_NUMBER_SWAPS 
                WHERE SWAP_ID = :swap_id
                """
                
                cursor.execute(select_sql, {'swap_id': swap_id})
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return AchAccountSwapResponse(
                    swap_id=row[0],
                    original_dfi_account_number=row[1],
                    swap_account_number=row[2],
                    swap_memo=row[3],
                    created_by_user=row[4],
                    created_date=row[5],
                    updated_by_user=row[6],
                    updated_date=row[7]
                )
                
        except Exception as e:
            logger.error(f"Failed to get ACH_ACCOUNT_NUMBER_SWAPS record {swap_id}: {e}")
            raise
    
    def get_ach_account_swaps(
        self,
        limit: int = 100,
        offset: int = 0,
        original_dfi_account_number: Optional[str] = None,
        swap_account_number: Optional[str] = None,
        swap_memo: Optional[str] = None
    ) -> List[AchAccountSwapResponse]:
        """Get list of ACH_ACCOUNT_NUMBER_SWAPS records with optional filtering."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause dynamically
                where_conditions = []
                params = {}
                
                if original_dfi_account_number is not None:
                    where_conditions.append("ORIGINAL_DFI_ACCOUNT_NUMBER = :original_dfi_account_number")
                    params['original_dfi_account_number'] = original_dfi_account_number
                
                if swap_account_number is not None:
                    where_conditions.append("SWAP_ACCOUNT_NUMBER = :swap_account_number")
                    params['swap_account_number'] = swap_account_number
                
                if swap_memo is not None:
                    where_conditions.append("UPPER(SWAP_MEMO) LIKE UPPER(:swap_memo)")
                    params['swap_memo'] = f'%{swap_memo}%'
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                select_sql = f"""
                SELECT 
                    SWAP_ID,
                    ORIGINAL_DFI_ACCOUNT_NUMBER,
                    SWAP_ACCOUNT_NUMBER,
                    SWAP_MEMO,
                    CREATED_BY_USER,
                    CREATED_DATE,
                    UPDATED_BY_USER,
                    UPDATED_DATE
                FROM {self.config.db_schema}.ACH_ACCOUNT_NUMBER_SWAPS 
                WHERE {where_clause}
                ORDER BY CREATED_DATE DESC
                OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
                """
                
                params['offset'] = offset
                params['limit'] = limit
                
                cursor.execute(select_sql, params)
                rows = cursor.fetchall()
                
                swaps = []
                for row in rows:
                    swaps.append(AchAccountSwapResponse(
                        swap_id=row[0],
                        original_dfi_account_number=row[1],
                        swap_account_number=row[2],
                        swap_memo=row[3],
                        created_by_user=row[4],
                        created_date=row[5],
                        updated_by_user=row[6],
                        updated_date=row[7]
                    ))
                
                logger.info(f"Retrieved {len(swaps)} ACH_ACCOUNT_NUMBER_SWAPS records")
                return swaps
                
        except Exception as e:
            logger.error(f"Failed to get ACH_ACCOUNT_NUMBER_SWAPS records: {e}")
            raise
    
    def get_ach_account_swaps_count(
        self,
        original_dfi_account_number: Optional[str] = None,
        swap_account_number: Optional[str] = None,
        swap_memo: Optional[str] = None
    ) -> int:
        """Get total count of ACH_ACCOUNT_NUMBER_SWAPS records with optional filtering."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause dynamically
                where_conditions = []
                params = {}
                
                if original_dfi_account_number is not None:
                    where_conditions.append("ORIGINAL_DFI_ACCOUNT_NUMBER = :original_dfi_account_number")
                    params['original_dfi_account_number'] = original_dfi_account_number
                
                if swap_account_number is not None:
                    where_conditions.append("SWAP_ACCOUNT_NUMBER = :swap_account_number")
                    params['swap_account_number'] = swap_account_number
                
                if swap_memo is not None:
                    where_conditions.append("UPPER(SWAP_MEMO) LIKE UPPER(:swap_memo)")
                    params['swap_memo'] = f'%{swap_memo}%'
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                count_sql = f"""
                SELECT COUNT(*) 
                FROM {self.config.db_schema}.ACH_ACCOUNT_NUMBER_SWAPS 
                WHERE {where_clause}
                """
                
                cursor.execute(count_sql, params)
                count = cursor.fetchone()[0]
                
                return count
                
        except Exception as e:
            logger.error(f"Failed to get ACH_ACCOUNT_NUMBER_SWAPS count: {e}")
            raise
    
    def get_swap_by_original_account(self, original_dfi_account_number: str) -> Optional[SwapLookupResponse]:
        """Get swap information by ORIGINAL_DFI_ACCOUNT_NUMBER (returns first match)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                select_sql = f"""
                SELECT 
                    SWAP_ID,
                    ORIGINAL_DFI_ACCOUNT_NUMBER,
                    SWAP_ACCOUNT_NUMBER,
                    SWAP_MEMO
                FROM {self.config.db_schema}.ACH_ACCOUNT_NUMBER_SWAPS 
                WHERE ORIGINAL_DFI_ACCOUNT_NUMBER = :original_dfi_account_number
                ORDER BY CREATED_DATE DESC
                FETCH FIRST 1 ROWS ONLY
                """
                
                cursor.execute(select_sql, {'original_dfi_account_number': original_dfi_account_number})
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return SwapLookupResponse(
                    swap_id=row[0],
                    original_dfi_account_number=row[1],
                    swap_account_number=row[2],
                    swap_memo=row[3]
                )
                
        except Exception as e:
            logger.error(f"Failed to get swap by ORIGINAL_DFI_ACCOUNT_NUMBER {original_dfi_account_number}: {e}")
            raise
    
    def update_ach_account_swap(self, swap_id: int, swap: AchAccountSwapUpdate) -> bool:
        """Update a ACH_ACCOUNT_NUMBER_SWAPS record by SWAP_ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build update fields dynamically
                update_fields = []
                params = {'swap_id': swap_id}
                
                if swap.original_dfi_account_number is not None:
                    update_fields.append("ORIGINAL_DFI_ACCOUNT_NUMBER = :original_dfi_account_number")
                    params['original_dfi_account_number'] = swap.original_dfi_account_number
                
                if swap.swap_account_number is not None:
                    update_fields.append("SWAP_ACCOUNT_NUMBER = :swap_account_number")
                    params['swap_account_number'] = swap.swap_account_number
                
                if swap.swap_memo is not None:
                    update_fields.append("SWAP_MEMO = :swap_memo")
                    params['swap_memo'] = swap.swap_memo
                
                if swap.updated_by_user is not None:
                    update_fields.append("UPDATED_BY_USER = :updated_by_user")
                    params['updated_by_user'] = swap.updated_by_user
                
                if not update_fields:
                    return False  # No fields to update
                
                update_fields.append("UPDATED_DATE = CURRENT_TIMESTAMP")
                
                update_sql = f"""
                UPDATE {self.config.db_schema}.ACH_ACCOUNT_NUMBER_SWAPS 
                SET {', '.join(update_fields)}
                WHERE SWAP_ID = :swap_id
                """
                
                cursor.execute(update_sql, params)
                conn.commit()
                
                rows_affected = cursor.rowcount
                logger.info(f"Updated ACH_ACCOUNT_NUMBER_SWAPS record {swap_id}, rows affected: {rows_affected}")
                return rows_affected > 0
                
        except Exception as e:
            logger.error(f"Failed to update ACH_ACCOUNT_NUMBER_SWAPS record {swap_id}: {e}")
            raise
    
    def update_swap_by_original_account(
        self,
        original_dfi_account_number: str,
        swap_account_number: Optional[str],
        swap_memo: str,
        updated_by_user: Optional[str] = None
    ) -> bool:
        """Update SWAP_ACCOUNT_NUMBER and SWAP_MEMO by ORIGINAL_DFI_ACCOUNT_NUMBER."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                update_fields = []
                params = {'original_dfi_account_number': original_dfi_account_number}
                
                if swap_account_number is not None:
                    update_fields.append("SWAP_ACCOUNT_NUMBER = :swap_account_number")
                    params['swap_account_number'] = swap_account_number
                
                update_fields.append("SWAP_MEMO = :swap_memo")
                params['swap_memo'] = swap_memo
                
                if updated_by_user is not None:
                    update_fields.append("UPDATED_BY_USER = :updated_by_user")
                    params['updated_by_user'] = updated_by_user
                
                update_fields.append("UPDATED_DATE = CURRENT_TIMESTAMP")
                
                update_sql = f"""
                UPDATE {self.config.db_schema}.ACH_ACCOUNT_NUMBER_SWAPS 
                SET {', '.join(update_fields)}
                WHERE ORIGINAL_DFI_ACCOUNT_NUMBER = :original_dfi_account_number
                """
                
                cursor.execute(update_sql, params)
                conn.commit()
                
                rows_affected = cursor.rowcount
                logger.info(f"Updated swap by ORIGINAL_DFI_ACCOUNT_NUMBER {original_dfi_account_number}, rows affected: {rows_affected}")
                return rows_affected > 0
                
        except Exception as e:
            logger.error(f"Failed to update swap by ORIGINAL_DFI_ACCOUNT_NUMBER {original_dfi_account_number}: {e}")
            raise
    
    def delete_ach_account_swap(self, swap_id: int) -> bool:
        """Delete a ACH_ACCOUNT_NUMBER_SWAPS record by SWAP_ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                delete_sql = f"DELETE FROM {self.config.db_schema}.ACH_ACCOUNT_NUMBER_SWAPS WHERE SWAP_ID = :swap_id"
                cursor.execute(delete_sql, {'swap_id': swap_id})
                conn.commit()
                
                rows_affected = cursor.rowcount
                logger.info(f"Deleted ACH_ACCOUNT_NUMBER_SWAPS record {swap_id}, rows affected: {rows_affected}")
                return rows_affected > 0
                
        except Exception as e:
            logger.error(f"Failed to delete ACH_ACCOUNT_NUMBER_SWAPS record {swap_id}: {e}")
            raise
    
    def delete_swap_by_original_account(self, original_dfi_account_number: str) -> bool:
        """Delete swap(s) by ORIGINAL_DFI_ACCOUNT_NUMBER."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                delete_sql = f"DELETE FROM {self.config.db_schema}.ACH_ACCOUNT_NUMBER_SWAPS WHERE ORIGINAL_DFI_ACCOUNT_NUMBER = :original_dfi_account_number"
                cursor.execute(delete_sql, {'original_dfi_account_number': original_dfi_account_number})
                conn.commit()
                
                rows_affected = cursor.rowcount
                logger.info(f"Deleted swap(s) by ORIGINAL_DFI_ACCOUNT_NUMBER {original_dfi_account_number}, rows affected: {rows_affected}")
                return rows_affected > 0
                
        except Exception as e:
            logger.error(f"Failed to delete swap by ORIGINAL_DFI_ACCOUNT_NUMBER {original_dfi_account_number}: {e}")
            raise
    
    def update_ach_entry_detail_with_swap(
        self,
        entry_detail_id: int,
        original_dfi_account_number: str,
        updated_by_user: Optional[str] = None
    ) -> bool:
        """Update ACH_ENTRY_DETAIL using swap by ORIGINAL_DFI_ACCOUNT_NUMBER and ENTRY_DETAIL_ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # First, get the swap information
                swap = self.get_swap_by_original_account(original_dfi_account_number)
                if not swap or not swap.swap_account_number:
                    logger.warning(f"No swap found for ORIGINAL_DFI_ACCOUNT_NUMBER {original_dfi_account_number}")
                    return False
                
                # Update the ACH_ENTRY_DETAIL record
                update_fields = []
                params = {'entry_detail_id': entry_detail_id}
                
                update_fields.append("DFI_ACCOUNT_NUMBER = :swap_account_number")
                params['swap_account_number'] = swap.swap_account_number
                
                if updated_by_user is not None:
                    # Note: ACH_ENTRY_DETAIL might not have UPDATED_BY_USER field
                    # We'll just update the account number
                    pass
                
                update_sql = f"""
                UPDATE {self.config.db_schema}.ACH_ENTRY_DETAIL 
                SET {', '.join(update_fields)}
                WHERE ENTRY_DETAIL_ID = :entry_detail_id
                """
                
                cursor.execute(update_sql, params)
                conn.commit()
                
                rows_affected = cursor.rowcount
                logger.info(f"Updated ACH_ENTRY_DETAIL {entry_detail_id} with swap account {swap.swap_account_number}, rows affected: {rows_affected}")
                return rows_affected > 0
                
        except Exception as e:
            logger.error(f"Failed to update ACH_ENTRY_DETAIL {entry_detail_id} with swap: {e}")
            raise
