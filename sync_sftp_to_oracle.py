#!/usr/bin/env python3
"""Test application to sync SFTP files to Oracle ACH_FILES table and process ACH lines."""

import sys
import requests
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from obs_sftp_file_processor.config import config
from obs_sftp_file_processor.oracle_service import OracleService
from obs_sftp_file_processor.oracle_models import AchFileCreate
from obs_sftp_file_processor.ach_file_lines_service import AchFileLinesService
from obs_sftp_file_processor.ach_validator import parse_ach_file_content, ACHLineValidation
from loguru import logger


class SftpToOracleSync:
    """Service to sync files from SFTP to Oracle database."""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """Initialize the sync service."""
        self.api_base_url = api_base_url
        self.oracle_service = OracleService(config.oracle)
        self.ach_file_lines_service = AchFileLinesService(config.oracle)
    
    def get_sftp_files(self) -> List[Dict[str, Any]]:
        """Get list of files from SFTP via API."""
        try:
            response = requests.get(f"{self.api_base_url}/files?path=upload")
            response.raise_for_status()
            data = response.json()
            return data.get('files', [])
        except Exception as e:
            logger.error(f"Failed to get SFTP files: {e}")
            raise
    
    def get_file_content(self, filename: str) -> Dict[str, Any]:
        """Get file content from SFTP via API."""
        try:
            # Use full path from upload directory
            file_path = f"upload/{filename}"
            response = requests.get(f"{self.api_base_url}/file/{file_path}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get file content for {filename}: {e}")
            raise
    
    def sync_files_to_oracle(self) -> Dict[str, Any]:
        """Sync all SFTP files to Oracle ACH_FILES table."""
        logger.info("Starting SFTP to Oracle sync process")
        
        results = {
            'total_files': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'errors': []
        }
        
        try:
            # Get list of files from SFTP
            logger.info("Fetching files from SFTP...")
            sftp_files = self.get_sftp_files()
            results['total_files'] = len(sftp_files)
            
            logger.info(f"Found {len(sftp_files)} files in SFTP")
            
            # Connect to Oracle
            with self.oracle_service as oracle:
                logger.info("Connected to Oracle database")
                
                # Process each file
                for file_info in sftp_files:
                    filename = file_info['name']
                    logger.info(f"Processing file: {filename}")
                    
                    try:
                        # Get file content
                        file_content = self.get_file_content(filename)
                        
                        # Create ACH_FILES record
                        ach_file = AchFileCreate(
                            original_filename=filename,
                            processing_status="Pending",
                            file_contents=file_content['content'],
                            created_by_user="UnityBankUserName@UB.com"
                        )
                        
                        # Insert into Oracle
                        file_id = oracle.create_ach_file(ach_file)
                        
                        logger.info(f"Successfully synced {filename} to Oracle with ID: {file_id}")
                        results['successful_syncs'] += 1
                        
                    except Exception as e:
                        error_msg = f"Failed to sync {filename}: {e}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['failed_syncs'] += 1
                
        except Exception as e:
            error_msg = f"Sync process failed: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        logger.info(f"Sync completed: {results['successful_syncs']}/{results['total_files']} files synced successfully")
        return results
    
    def test_oracle_connection(self) -> bool:
        """Test Oracle database connection."""
        try:
            with self.oracle_service as oracle:
                # Try to get count of ACH_FILES
                count = oracle.get_ach_files_count()
                logger.info(f"Oracle connection successful. ACH_FILES table has {count} records.")
                return True
        except Exception as e:
            logger.error(f"Oracle connection test failed: {e}")
            return False
    
    def process_ach_file_lines(self, file_id: int, file_content: str) -> Dict[str, Any]:
        """Process ACH file content and create ACH_FILE_LINES records."""
        logger.info(f"Processing ACH file lines for FILE_ID: {file_id}")
        
        results = {
            'total_lines': 0,
            'valid_lines': 0,
            'invalid_lines': 0,
            'lines_created': 0,
            'errors': []
        }
        
        try:
            # Parse and validate ACH file content
            line_validations = parse_ach_file_content(file_content)
            results['total_lines'] = len(line_validations)
            
            logger.info(f"Found {len(line_validations)} lines to process")
            
            # Delete existing lines for this file
            with self.ach_file_lines_service as ach_lines_service:
                deleted_count = ach_lines_service.delete_lines_by_file_id(file_id)
                logger.info(f"Deleted {deleted_count} existing ACH_FILE_LINES records")
                
                # Prepare batch data for insertion
                batch_data = []
                
                for validation in line_validations:
                    # Count valid/invalid lines
                    if validation.is_valid:
                        results['valid_lines'] += 1
                    else:
                        results['invalid_lines'] += 1
                    
                    # Prepare line data
                    line_data = {
                        'line_number': validation.line_number,
                        'line_content': validation.line_content,
                        'line_errors': '; '.join(validation.errors) if validation.errors else None,
                        'created_by_user': 'UnityBankUserName@UB.com'
                    }
                    batch_data.append(line_data)
                
                # Insert all lines in batch
                if batch_data:
                    lines_created = ach_lines_service.create_ach_file_lines_batch(file_id, batch_data)
                    results['lines_created'] = lines_created
                    logger.info(f"Created {lines_created} ACH_FILE_LINES records")
                
        except Exception as e:
            error_msg = f"Failed to process ACH file lines for FILE_ID {file_id}: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def process_pending_ach_files(self) -> Dict[str, Any]:
        """Process all ACH_FILES with status 'Pending' and create ACH_FILE_LINES."""
        logger.info("Processing pending ACH files")
        
        results = {
            'files_processed': 0,
            'total_lines_created': 0,
            'files_with_errors': 0,
            'errors': []
        }
        
        try:
            with self.oracle_service as oracle:
                # Get all files with status 'Pending'
                all_files = oracle.get_ach_files(limit=1000)  # Get all files
                pending_files = [f for f in all_files if f.processing_status == 'Pending']
                
                logger.info(f"Found {len(pending_files)} files with status 'Pending'")
                
                for ach_file in pending_files:
                    try:
                        logger.info(f"Processing file: {ach_file.original_filename} (ID: {ach_file.file_id})")
                        
                        # Process ACH file lines
                        line_results = self.process_ach_file_lines(ach_file.file_id, ach_file.file_contents)
                        
                        # Update results
                        results['files_processed'] += 1
                        results['total_lines_created'] += line_results['lines_created']
                        
                        # Update file status to 'Processed'
                        from obs_sftp_file_processor.oracle_models import AchFileUpdate
                        update_data = AchFileUpdate(
                            processing_status='Processed',
                            updated_by_user='UnityBankUserName@UB.com'
                        )
                        oracle.update_ach_file(ach_file.file_id, update_data)
                        
                        logger.info(f"Successfully processed {ach_file.original_filename}: {line_results['lines_created']} lines created")
                        
                    except Exception as e:
                        error_msg = f"Failed to process file {ach_file.original_filename} (ID: {ach_file.file_id}): {e}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['files_with_errors'] += 1
                
        except Exception as e:
            error_msg = f"Failed to process pending ACH files: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        logger.info(f"Processed {results['files_processed']} files, created {results['total_lines_created']} lines")
        return results
    
    def test_sftp_connection(self) -> bool:
        """Test SFTP connection via API."""
        try:
            response = requests.get(f"{self.api_base_url}/health")
            response.raise_for_status()
            logger.info("SFTP connection via API successful")
            return True
        except Exception as e:
            logger.error(f"SFTP connection test failed: {e}")
            return False


def main():
    """Main function to run the sync process."""
    print("🔄 SFTP to Oracle Sync and ACH Processing Application")
    print("=" * 60)
    
    # Initialize sync service
    sync_service = SftpToOracleSync()
    
    # Test connections
    print("\n1. Testing connections...")
    
    sftp_ok = sync_service.test_sftp_connection()
    oracle_ok = sync_service.test_oracle_connection()
    
    if not sftp_ok:
        print("❌ SFTP connection failed")
        return
    
    if not oracle_ok:
        print("❌ Oracle connection failed")
        return
    
    print("✅ All connections successful")
    
    # Run SFTP to Oracle sync process
    print("\n2. Starting SFTP to Oracle sync process...")
    sync_results = sync_service.sync_files_to_oracle()
    
    # Display sync results
    print("\n3. SFTP Sync Results:")
    print(f"   Total files found: {sync_results['total_files']}")
    print(f"   Successfully synced: {sync_results['successful_syncs']}")
    print(f"   Failed syncs: {sync_results['failed_syncs']}")
    
    if sync_results['errors']:
        print("\n4. Sync Errors:")
        for error in sync_results['errors']:
            print(f"   ❌ {error}")
    
    # Process ACH file lines
    print("\n5. Processing ACH file lines...")
    line_results = sync_service.process_pending_ach_files()
    
    # Display line processing results
    print("\n6. ACH Line Processing Results:")
    print(f"   Files processed: {line_results['files_processed']}")
    print(f"   Total lines created: {line_results['total_lines_created']}")
    print(f"   Files with errors: {line_results['files_with_errors']}")
    
    if line_results['errors']:
        print("\n7. Line Processing Errors:")
        for error in line_results['errors']:
            print(f"   ❌ {error}")
    
    print(f"\n🎉 Complete process finished!")
    
    if sync_results['successful_syncs'] > 0:
        print(f"✅ {sync_results['successful_syncs']} files successfully loaded into Oracle ACH_FILES table")
    
    if line_results['total_lines_created'] > 0:
        print(f"✅ {line_results['total_lines_created']} ACH lines successfully processed and stored")
    
    if sync_results['successful_syncs'] == 0 and line_results['total_lines_created'] == 0:
        print("⚠️  No files were processed")


if __name__ == "__main__":
    main()
