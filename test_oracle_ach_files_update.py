"""Test for updating ACH_FILES by file_id and verifying audit record creation."""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from obs_sftp_file_processor.config import config
from obs_sftp_file_processor.oracle_service import OracleService
from obs_sftp_file_processor.oracle_models import AchFileCreate, AchFileUpdateByFileIdRequest
from loguru import logger
import httpx


def test_oracle_ach_files_update():
    """Test updating ACH_FILES by file_id and verify audit record creation."""
    
    logger.info("🧪 Testing ACH_FILES update by file_id with audit verification")
    logger.info("=" * 70)
    
    # Set Oracle environment variables
    os.environ['ORACLE_HOME'] = os.path.expanduser('~/oracle/instantclient_23_3')
    os.environ['DYLD_LIBRARY_PATH'] = f"{os.environ['ORACLE_HOME']}:{os.environ.get('DYLD_LIBRARY_PATH', '')}"
    
    # Initialize services
    oracle_service = OracleService(config.oracle)
    api_base_url = "http://localhost:8000"
    
    test_file_id = None
    
    try:
        # Step 1: Create a test ACH_FILES record
        logger.info("\n📝 Step 1: Creating test ACH_FILES record...")
        with oracle_service:
            test_ach_file = AchFileCreate(
                original_filename="test_update_file.txt",
                processing_status="Pending",
                file_contents="Original file content for testing update functionality.",
                created_by_user="test_user@example.com"
            )
            test_file_id = oracle_service.create_ach_file(test_ach_file)
            logger.info(f"✅ Created test ACH_FILES record with FILE_ID: {test_file_id}")
        
        # Step 2: Get initial state from ACH_FILES
        logger.info("\n📖 Step 2: Getting initial ACH_FILES record...")
        with oracle_service:
            initial_file = oracle_service.get_ach_file(test_file_id)
            if not initial_file:
                raise ValueError(f"Test file with FILE_ID {test_file_id} not found")
            logger.info(f"✅ Initial file contents: {initial_file.file_contents[:50]}...")
        
        # Step 3: Get initial audit records count
        logger.info("\n🔍 Step 3: Getting initial AUDIT_ACH_FILES records...")
        with oracle_service:
            initial_audit_records = oracle_service.get_audit_ach_files_by_file_id(test_file_id)
            initial_audit_count = len(initial_audit_records)
            logger.info(f"✅ Initial audit records count: {initial_audit_count}")
        
        # Step 4: Call the API endpoint to update the file
        logger.info("\n🔄 Step 4: Calling API endpoint to update ACH_FILES...")
        updated_content = "Updated file content with new data for testing audit functionality."
        update_request = AchFileUpdateByFileIdRequest(
            file_contents=updated_content,
            updated_by_user="system-user"
        )
        
        response = httpx.post(
            f"{api_base_url}/oracle/ach-files-update-by-file-id/{test_file_id}",
            json=update_request.model_dump(),
            timeout=30
        )
        
        if response.status_code != 200:
            raise ValueError(f"API update failed with status {response.status_code}: {response.text}")
        
        updated_file_response = response.json()
        logger.info(f"✅ API update successful. Updated file contents: {updated_file_response['file_contents'][:50]}...")
        
        # Step 5: Verify the update in ACH_FILES table
        logger.info("\n✅ Step 5: Verifying update in ACH_FILES table...")
        with oracle_service:
            updated_file = oracle_service.get_ach_file(test_file_id)
            if not updated_file:
                raise ValueError(f"Updated file with FILE_ID {test_file_id} not found")
            
            # Verify file_contents
            if updated_file.file_contents != updated_content:
                raise ValueError(
                    f"File contents mismatch!\n"
                    f"Expected: {updated_content}\n"
                    f"Got: {updated_file.file_contents}"
                )
            
            # Verify updated_by_user
            if updated_file.updated_by_user != "system-user":
                raise ValueError(
                    f"Updated_by_user mismatch!\n"
                    f"Expected: system-user\n"
                    f"Got: {updated_file.updated_by_user}"
                )
            
            # Verify updated_date is set
            if not updated_file.updated_date:
                raise ValueError("Updated_date is not set!")
            
            logger.info(f"✅ ACH_FILES update verified:")
            logger.info(f"   - File contents: ✅ Updated")
            logger.info(f"   - Updated by user: ✅ {updated_file.updated_by_user}")
            logger.info(f"   - Updated date: ✅ {updated_file.updated_date}")
        
        # Step 6: Verify audit record was created in AUDIT_ACH_FILES
        logger.info("\n📋 Step 6: Verifying audit record in AUDIT_ACH_FILES table...")
        with oracle_service:
            audit_records = oracle_service.get_audit_ach_files_by_file_id(test_file_id)
            new_audit_count = len(audit_records)
            
            if new_audit_count <= initial_audit_count:
                raise ValueError(
                    f"Audit record was not created!\n"
                    f"Initial count: {initial_audit_count}\n"
                    f"New count: {new_audit_count}"
                )
            
            # Find the most recent audit record (should be the one created by the update)
            latest_audit = audit_records[0]  # Already sorted DESC by AUDIT_ID
            
            # Verify audit record matches the updated file
            if latest_audit['file_id'] != test_file_id:
                raise ValueError(f"Audit record FILE_ID mismatch: {latest_audit['file_id']} != {test_file_id}")
            
            if latest_audit['file_contents'] != updated_content:
                raise ValueError(
                    f"Audit record file_contents mismatch!\n"
                    f"Expected: {updated_content}\n"
                    f"Got: {latest_audit['file_contents']}"
                )
            
            if latest_audit['updated_by_user'] != "system-user":
                raise ValueError(
                    f"Audit record updated_by_user mismatch!\n"
                    f"Expected: system-user\n"
                    f"Got: {latest_audit['updated_by_user']}"
                )
            
            logger.info(f"✅ AUDIT_ACH_FILES record verified:")
            logger.info(f"   - AUDIT_ID: {latest_audit['audit_id']}")
            logger.info(f"   - FILE_ID: {latest_audit['file_id']}")
            logger.info(f"   - File contents: ✅ Matches updated content")
            logger.info(f"   - Updated by user: ✅ {latest_audit['updated_by_user']}")
            logger.info(f"   - Updated date: ✅ {latest_audit['updated_date']}")
        
        # Cleanup: Delete test record
        logger.info("\n🧹 Cleanup: Deleting test ACH_FILES record...")
        with oracle_service:
            oracle_service.delete_ach_file(test_file_id)
            logger.info(f"✅ Test record {test_file_id} deleted")
        
        logger.info("\n" + "=" * 70)
        logger.info("🎉 All tests passed! ACH_FILES update and audit record creation verified.")
        return True
        
    except httpx.RequestError as e:
        logger.error(f"❌ API request failed: {e}")
        logger.error("Make sure the FastAPI server is running on http://localhost:8000")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        # Cleanup on error
        if test_file_id:
            try:
                with oracle_service:
                    oracle_service.delete_ach_file(test_file_id)
                    logger.info(f"Cleaned up test record {test_file_id}")
            except:
                pass
        return False


if __name__ == "__main__":
    logger.info("🚀 Starting ACH_FILES update and audit test...")
    success = test_oracle_ach_files_update()
    sys.exit(0 if success else 1)
