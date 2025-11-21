"""Oracle database service for ACH_FILES table operations."""

import os
import oracledb
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from .oracle_config import OracleConfig
from .oracle_models import AchFileCreate, AchFileUpdate, AchFileResponse


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
        """Create a new ACH_FILES record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert statement with RETURNING clause to get the generated FILE_ID
                insert_sql = """
                INSERT INTO ACH_FILES (
                    ORIGINAL_FILENAME,
                    PROCESSING_STATUS,
                    FILE_CONTENTS,
                    CREATED_BY_USER,
                    CREATED_DATE
                ) VALUES (
                    :original_filename,
                    :processing_status,
                    :file_contents,
                    :created_by_user,
                    CURRENT_TIMESTAMP
                ) RETURNING FILE_ID INTO :file_id
                """
                
                # Execute insert
                file_id = cursor.var(int)
                cursor.execute(insert_sql, {
                    'original_filename': ach_file.original_filename,
                    'processing_status': ach_file.processing_status,
                    'file_contents': ach_file.file_contents,
                    'created_by_user': ach_file.created_by_user,
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
                    UPDATED_DATE
                FROM ACH_FILES 
                WHERE FILE_ID = :file_id
                """
                
                cursor.execute(select_sql, {'file_id': file_id})
                row = cursor.fetchone()
                
                if row:
                    # Handle CLOB data - convert LOB to string
                    file_contents = row[3]
                    if hasattr(file_contents, 'read'):
                        # It's a LOB object, read the content
                        file_contents = file_contents.read()
                    
                    return AchFileResponse(
                        file_id=row[0],
                        original_filename=row[1],
                        processing_status=row[2],
                        file_contents=file_contents,
                        created_by_user=row[4],
                        created_date=row[5],
                        updated_by_user=row[6],
                        updated_date=row[7]
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
                    FILE_CONTENTS,
                    CREATED_BY_USER,
                    CREATED_DATE,
                    UPDATED_BY_USER,
                    UPDATED_DATE
                FROM ACH_FILES 
                WHERE NOT (ORIGINAL_FILENAME LIKE 'FEDACHOUT%' OR ORIGINAL_FILENAME LIKE '%.pdf')
                ORDER BY CREATED_DATE DESC
                OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
                """
                
                cursor.execute(select_sql, {'limit': limit, 'offset': offset})
                rows = cursor.fetchall()
                
                files = []
                for row in rows:
                    # Handle CLOB data - convert LOB to string
                    file_contents = row[3]
                    if file_contents and hasattr(file_contents, 'read'):
                        # It's a LOB object, read the content
                        file_contents = file_contents.read()
                    
                    files.append(AchFileResponse(
                        file_id=row[0],
                        original_filename=row[1],
                        processing_status=row[2],
                        file_contents=file_contents,
                        created_by_user=row[4],
                        created_date=row[5],
                        updated_by_user=row[6],
                        updated_date=row[7]
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
                file_contents_size = len(ach_file.file_contents.encode('utf-8')) if ach_file.file_contents else 0
                use_lob_update = file_contents_size > 1048576  # 1MB threshold
                
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
                file_contents_size = len(file_contents.encode('utf-8'))
                use_lob_update = file_contents_size > 1048576  # 1MB threshold
                
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
                    UPDATED_DATE
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
                        'updated_date': row[8]
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
    
    def check_email_password_hash(self, email: str, password_hash: str) -> Dict[str, Any]:
        """
        Check if email and password hash match in API_USERS table.
        
        Args:
            email: User email address
            password_hash: Password hash to verify
            
        Returns:
            Dictionary with:
            - authenticated: bool - True if match found
            - is_admin: bool - True if user is admin (only when authenticated=True)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Query API_USERS table for matching email and password_hash
                # Also check that user is active, and get IS_ADMIN
                select_sql = """
                SELECT IS_ADMIN
                FROM API_USERS
                WHERE UPPER(EMAIL) = UPPER(:email)
                  AND PASSWORD_HASH = :password_hash
                  AND IS_ACTIVE = 1
                """
                
                cursor.execute(select_sql, {
                    'email': email,
                    'password_hash': password_hash
                })
                
                result = cursor.fetchone()
                
                if result:
                    is_admin = bool(result[0]) if result[0] is not None else False
                    logger.info(f"Email and password hash match found for: {email} (IS_ADMIN: {is_admin})")
                    return {
                        'authenticated': True,
                        'is_admin': is_admin
                    }
                else:
                    logger.info(f"No match found for email: {email}")
                    return {
                        'authenticated': False,
                        'is_admin': False
                    }
                
        except Exception as e:
            logger.error(f"Failed to check email and password hash: {e}")
            raise
