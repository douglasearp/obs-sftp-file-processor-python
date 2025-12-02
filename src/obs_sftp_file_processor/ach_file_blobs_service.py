"""Oracle database service for ACH_FILES_BLOBS table operations."""

import oracledb
from typing import Optional
from datetime import datetime
from loguru import logger
from .oracle_config import OracleConfig
from .ach_file_blobs_models import AchFileBlobCreate, AchFileBlobUpdate, AchFileBlobResponse


class AchFileBlobsService:
    """Service for ACH_FILES_BLOBS database operations."""
    
    def __init__(self, config: OracleConfig):
        """Initialize ACH_FILES_BLOBS service with configuration."""
        self.config = config
        self.pool: Optional[oracledb.ConnectionPool] = None
    
    def connect(self) -> None:
        """Establish Oracle connection pool.
        
        Uses the same connection logic as OracleService.
        """
        import os
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
                    try:
                        oracledb.init_oracle_client()
                        logger.info("Oracle thick mode initialized without lib_dir")
                        use_thick_mode = True
                    except Exception as e2:
                        logger.warning(f"Thick mode fallback failed: {e2}")
                        logger.info("Using thin mode (no encryption support)")
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
    
    def create_ach_file_blob(self, ach_file_blob: AchFileBlobCreate) -> int:
        """Create a new ACH_FILES_BLOBS record.
        
        For large CLOB inserts (>1MB), uses DBMS_LOB to reduce PGA memory usage.
        This prevents ORA-04036 errors when inserting large file contents.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check file size to determine insert method
                # Use more conservative threshold (500KB) and check both string length and encoded size
                if ach_file_blob.file_contents:
                    char_length = len(ach_file_blob.file_contents)
                    byte_size = len(ach_file_blob.file_contents.encode('utf-8'))
                    file_contents_size = max(char_length, byte_size)
                else:
                    file_contents_size = 0
                # Lower threshold to 500KB to be more conservative and prevent edge cases
                use_lob_insert = file_contents_size > 512 * 1024  # 500KB threshold
                
                if use_lob_insert:
                    # For large CLOBs, insert with empty CLOB first, then write using DBMS_LOB
                    # Use PL/SQL block to get CLOB locator
                    insert_plsql = """
                    DECLARE
                        v_file_blob_id NUMBER;
                        v_clob CLOB;
                    BEGIN
                        INSERT INTO ACH_FILES_BLOBS (
                            FILE_ID,
                            ORIGINAL_FILENAME,
                            PROCESSING_STATUS,
                            FILE_CONTENTS,
                            CREATED_BY_USER,
                            CREATED_DATE
                        ) VALUES (
                            :file_id,
                            :original_filename,
                            :processing_status,
                            EMPTY_CLOB(),
                            :created_by_user,
                            CURRENT_TIMESTAMP
                        ) RETURNING FILE_BLOB_ID, FILE_CONTENTS INTO v_file_blob_id, v_clob;
                        
                        :file_blob_id := v_file_blob_id;
                        :file_contents_clob := v_clob;
                    END;
                    """
                    
                    # Execute insert with empty CLOB
                    file_blob_id = cursor.var(int)
                    file_contents_clob = cursor.var(oracledb.DB_TYPE_CLOB)
                    cursor.execute(insert_plsql, {
                        'file_id': ach_file_blob.file_id,
                        'original_filename': ach_file_blob.original_filename,
                        'processing_status': ach_file_blob.processing_status,
                        'created_by_user': ach_file_blob.created_by_user,
                        'file_blob_id': file_blob_id,
                        'file_contents_clob': file_contents_clob
                    })
                    
                    # Get the CLOB locator
                    clob = file_contents_clob.getvalue()[0]
                    generated_id = file_blob_id.getvalue()[0]
                    
                    # Write content in 32KB chunks to avoid PGA memory issues
                    chunk_size = 32767  # Oracle VARCHAR2 max size
                    file_contents = ach_file_blob.file_contents
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
                    logger.info(f"Created ACH_FILES_BLOBS record {generated_id} with large CLOB ({file_contents_size} bytes) using DBMS_LOB")
                    return generated_id
                
                # For small CLOBs, use standard INSERT
                insert_sql = """
                INSERT INTO ACH_FILES_BLOBS (
                    FILE_ID,
                    ORIGINAL_FILENAME,
                    PROCESSING_STATUS,
                    FILE_CONTENTS,
                    CREATED_BY_USER,
                    CREATED_DATE
                ) VALUES (
                    :file_id,
                    :original_filename,
                    :processing_status,
                    :file_contents,
                    :created_by_user,
                    CURRENT_TIMESTAMP
                ) RETURNING FILE_BLOB_ID INTO :file_blob_id
                """
                
                # Execute insert
                file_blob_id = cursor.var(int)
                cursor.execute(insert_sql, {
                    'file_id': ach_file_blob.file_id,
                    'original_filename': ach_file_blob.original_filename,
                    'processing_status': ach_file_blob.processing_status,
                    'file_contents': ach_file_blob.file_contents,
                    'created_by_user': ach_file_blob.created_by_user,
                    'file_blob_id': file_blob_id
                })
                
                conn.commit()
                generated_id = file_blob_id.getvalue()[0]
                
                logger.info(f"Created ACH_FILES_BLOBS record with ID: {generated_id}")
                return generated_id
                
        except Exception as e:
            logger.error(f"Failed to create ACH_FILES_BLOBS record: {e}")
            raise
    
    def update_ach_file_blob_status(
        self, 
        file_blob_id: int, 
        status: str, 
        updated_by_user: Optional[str] = None
    ) -> None:
        """Update ACH_FILES_BLOBS processing status."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                update_sql = """
                UPDATE ACH_FILES_BLOBS
                SET PROCESSING_STATUS = :status,
                    UPDATED_DATE = CURRENT_TIMESTAMP,
                    UPDATED_BY_USER = :updated_by_user
                WHERE FILE_BLOB_ID = :file_blob_id
                """
                
                cursor.execute(update_sql, {
                    'status': status,
                    'updated_by_user': updated_by_user,
                    'file_blob_id': file_blob_id
                })
                
                conn.commit()
                logger.info(f"Updated ACH_FILES_BLOBS {file_blob_id} status to {status}")
                
        except Exception as e:
            logger.error(f"Failed to update ACH_FILES_BLOBS status: {e}")
            raise
    
    def get_ach_file_blob(self, file_blob_id: int) -> Optional[AchFileBlobResponse]:
        """Get an ACH_FILES_BLOBS record by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                select_sql = """
                SELECT 
                    FILE_BLOB_ID,
                    FILE_ID,
                    ORIGINAL_FILENAME,
                    PROCESSING_STATUS,
                    FILE_CONTENTS,
                    CREATED_BY_USER,
                    CREATED_DATE,
                    UPDATED_BY_USER,
                    UPDATED_DATE
                FROM ACH_FILES_BLOBS
                WHERE FILE_BLOB_ID = :file_blob_id
                """
                
                cursor.execute(select_sql, {'file_blob_id': file_blob_id})
                row = cursor.fetchone()
                
                if row:
                    return AchFileBlobResponse(
                        file_blob_id=row[0],
                        file_id=row[1],
                        original_filename=row[2],
                        processing_status=row[3],
                        file_contents=row[4].read() if row[4] else None,
                        created_by_user=row[5],
                        created_date=row[6],
                        updated_by_user=row[7],
                        updated_date=row[8]
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to get ACH_FILES_BLOBS record: {e}")
            raise
    
    def get_ach_file_blob_by_file_id(self, file_id: int) -> Optional[AchFileBlobResponse]:
        """Get an ACH_FILES_BLOBS record by FILE_ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                select_sql = """
                SELECT 
                    FILE_BLOB_ID,
                    FILE_ID,
                    ORIGINAL_FILENAME,
                    PROCESSING_STATUS,
                    FILE_CONTENTS,
                    CREATED_BY_USER,
                    CREATED_DATE,
                    UPDATED_BY_USER,
                    UPDATED_DATE
                FROM ACH_FILES_BLOBS
                WHERE FILE_ID = :file_id
                ORDER BY CREATED_DATE DESC
                FETCH FIRST 1 ROWS ONLY
                """
                
                cursor.execute(select_sql, {'file_id': file_id})
                row = cursor.fetchone()
                
                if row:
                    return AchFileBlobResponse(
                        file_blob_id=row[0],
                        file_id=row[1],
                        original_filename=row[2],
                        processing_status=row[3],
                        file_contents=row[4].read() if row[4] else None,
                        created_by_user=row[5],
                        created_date=row[6],
                        updated_by_user=row[7],
                        updated_date=row[8]
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to get ACH_FILES_BLOBS record by FILE_ID: {e}")
            raise

