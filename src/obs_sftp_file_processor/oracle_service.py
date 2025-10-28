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
        """Establish Oracle connection pool."""
        try:
            # Initialize thick mode for network encryption support
            try:
                oracledb.init_oracle_client(lib_dir=os.environ.get('ORACLE_HOME'))
                logger.info("Oracle thick mode initialized successfully")
            except Exception as e:
                logger.warning(f"Thick mode initialization failed: {e}")
                # Try without lib_dir
                try:
                    oracledb.init_oracle_client()
                    logger.info("Oracle thick mode initialized without lib_dir")
                except Exception as e2:
                    logger.error(f"Failed to initialize thick mode: {e2}")
                    raise
            
            # Create connection pool
            self.pool = oracledb.create_pool(
                user=self.config.username,
                password=self.config.password,
                dsn=self.config.dsn,
                min=self.config.min_pool_size,
                max=self.config.max_pool_size,
                increment=self.config.pool_increment
            )
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
        """Get list of ACH_FILES records."""
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
                ORDER BY CREATED_DATE DESC
                OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
                """
                
                cursor.execute(select_sql, {'limit': limit, 'offset': offset})
                rows = cursor.fetchall()
                
                files = []
                for row in rows:
                    # Handle CLOB data - convert LOB to string
                    file_contents = row[3]
                    if hasattr(file_contents, 'read'):
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
        """Update an ACH_FILES record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update statement
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
        """Get total count of ACH_FILES records."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                count_sql = "SELECT COUNT(*) FROM ACH_FILES"
                cursor.execute(count_sql)
                count = cursor.fetchone()[0]
                
                return count
                
        except Exception as e:
            logger.error(f"Failed to get ACH_FILES count: {e}")
            raise
