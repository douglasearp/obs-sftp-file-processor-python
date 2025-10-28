"""Oracle database service for ACH_FILE_LINES table operations."""

import os
import oracledb
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from .oracle_config import OracleConfig
from .ach_file_lines_models import AchFileLineCreate, AchFileLineUpdate, AchFileLineResponse


class AchFileLinesService:
    """Service for ACH_FILE_LINES database operations."""
    
    def __init__(self, config: OracleConfig):
        """Initialize ACH_FILE_LINES service with configuration."""
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
    
    def delete_lines_by_file_id(self, file_id: int) -> int:
        """Delete all ACH_FILE_LINES records for a specific FILE_ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                delete_sql = "DELETE FROM ACH_FILE_LINES WHERE FILE_ID = :file_id"
                cursor.execute(delete_sql, {'file_id': file_id})
                conn.commit()
                
                rows_affected = cursor.rowcount
                logger.info(f"Deleted {rows_affected} ACH_FILE_LINES records for FILE_ID: {file_id}")
                return rows_affected
                
        except Exception as e:
            logger.error(f"Failed to delete ACH_FILE_LINES records for FILE_ID {file_id}: {e}")
            raise
    
    def create_ach_file_line(self, ach_file_line: AchFileLineCreate) -> int:
        """Create a new ACH_FILE_LINES record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert statement with RETURNING clause to get the generated FILE_LINES_ID
                insert_sql = """
                INSERT INTO ACH_FILE_LINES (
                    FILE_ID,
                    LINE_NUMBER,
                    LINE_CONTENT,
                    LINE_ERRORS,
                    CREATED_BY_USER,
                    CREATED_DATE
                ) VALUES (
                    :file_id,
                    :line_number,
                    :line_content,
                    :line_errors,
                    :created_by_user,
                    CURRENT_TIMESTAMP
                ) RETURNING FILE_LINES_ID INTO :file_lines_id
                """
                
                # Execute insert
                file_lines_id = cursor.var(int)
                cursor.execute(insert_sql, {
                    'file_id': ach_file_line.file_id,
                    'line_number': ach_file_line.line_number,
                    'line_content': ach_file_line.line_content,
                    'line_errors': ach_file_line.line_errors,
                    'created_by_user': ach_file_line.created_by_user,
                    'file_lines_id': file_lines_id
                })
                
                conn.commit()
                generated_id = file_lines_id.getvalue()[0]
                
                logger.info(f"Created ACH_FILE_LINES record with ID: {generated_id}")
                return generated_id
                
        except Exception as e:
            logger.error(f"Failed to create ACH_FILE_LINES record: {e}")
            raise
    
    def create_ach_file_lines_batch(self, file_id: int, lines_data: List[Dict[str, Any]]) -> int:
        """Create multiple ACH_FILE_LINES records in a batch."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare batch insert
                insert_sql = """
                INSERT INTO ACH_FILE_LINES (
                    FILE_ID,
                    LINE_NUMBER,
                    LINE_CONTENT,
                    LINE_ERRORS,
                    CREATED_BY_USER,
                    CREATED_DATE
                ) VALUES (
                    :file_id,
                    :line_number,
                    :line_content,
                    :line_errors,
                    :created_by_user,
                    CURRENT_TIMESTAMP
                )"""
                
                # Prepare data for batch insert
                batch_data = []
                for line_data in lines_data:
                    batch_data.append({
                        'file_id': file_id,
                        'line_number': line_data['line_number'],
                        'line_content': line_data['line_content'],
                        'line_errors': line_data.get('line_errors'),
                        'created_by_user': line_data.get('created_by_user', 'UnityBankUserName@UB.com')
                    })
                
                # Execute batch insert
                cursor.executemany(insert_sql, batch_data)
                conn.commit()
                
                rows_created = len(batch_data)
                logger.info(f"Created {rows_created} ACH_FILE_LINES records for FILE_ID: {file_id}")
                return rows_created
                
        except Exception as e:
            logger.error(f"Failed to create ACH_FILE_LINES batch for FILE_ID {file_id}: {e}")
            raise
    
    def get_ach_file_lines(self, file_id: int, limit: int = 1000, offset: int = 0) -> List[AchFileLineResponse]:
        """Get ACH_FILE_LINES records for a specific FILE_ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                select_sql = """
                SELECT 
                    FILE_LINES_ID,
                    FILE_ID,
                    LINE_NUMBER,
                    LINE_CONTENT,
                    LINE_ERRORS,
                    CREATED_BY_USER,
                    CREATED_DATE,
                    UPDATED_BY_USER,
                    UPDATED_DATE
                FROM ACH_FILE_LINES 
                WHERE FILE_ID = :file_id
                ORDER BY LINE_NUMBER
                OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
                """
                
                cursor.execute(select_sql, {'file_id': file_id, 'limit': limit, 'offset': offset})
                rows = cursor.fetchall()
                
                lines = []
                for row in rows:
                    lines.append(AchFileLineResponse(
                        file_lines_id=row[0],
                        file_id=row[1],
                        line_number=row[2],
                        line_content=row[3],
                        line_errors=row[4],
                        created_by_user=row[5],
                        created_date=row[6],
                        updated_by_user=row[7],
                        updated_date=row[8]
                    ))
                
                logger.info(f"Retrieved {len(lines)} ACH_FILE_LINES records for FILE_ID: {file_id}")
                return lines
                
        except Exception as e:
            logger.error(f"Failed to get ACH_FILE_LINES records for FILE_ID {file_id}: {e}")
            raise
    
    def get_ach_file_lines_count(self, file_id: int) -> int:
        """Get count of ACH_FILE_LINES records for a specific FILE_ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                count_sql = "SELECT COUNT(*) FROM ACH_FILE_LINES WHERE FILE_ID = :file_id"
                cursor.execute(count_sql, {'file_id': file_id})
                count = cursor.fetchone()[0]
                
                return count
                
        except Exception as e:
            logger.error(f"Failed to get ACH_FILE_LINES count for FILE_ID {file_id}: {e}")
            raise
