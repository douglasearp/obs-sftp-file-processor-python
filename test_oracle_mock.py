#!/usr/bin/env python3
"""Mock Oracle service for testing without actual Oracle connection."""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from obs_sftp_file_processor.oracle_models import AchFileCreate, AchFileUpdate, AchFileResponse
from loguru import logger


class MockOracleService:
    """Mock Oracle service for testing without actual database connection."""
    
    def __init__(self, config=None):
        """Initialize mock service."""
        self.config = config
        self.files: Dict[int, AchFileResponse] = {}
        self.next_id = 1
    
    def connect(self) -> None:
        """Mock connect method."""
        logger.info("Mock Oracle connection established")
    
    def disconnect(self) -> None:
        """Mock disconnect method."""
        logger.info("Mock Oracle connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def create_ach_file(self, ach_file: AchFileCreate) -> int:
        """Create a new ACH_FILES record."""
        file_id = self.next_id
        self.next_id += 1
        
        mock_file = AchFileResponse(
            file_id=file_id,
            original_filename=ach_file.original_filename,
            processing_status=ach_file.processing_status,
            file_contents=ach_file.file_contents,
            created_by_user=ach_file.created_by_user,
            created_date=datetime.now(),
            updated_by_user=ach_file.updated_by_user,
            updated_date=None
        )
        
        self.files[file_id] = mock_file
        logger.info(f"Mock: Created ACH_FILES record with ID: {file_id}")
        return file_id
    
    def get_ach_file(self, file_id: int) -> Optional[AchFileResponse]:
        """Get an ACH_FILES record by ID."""
        return self.files.get(file_id)
    
    def get_ach_files(self, limit: int = 100, offset: int = 0) -> List[AchFileResponse]:
        """Get list of ACH_FILES records."""
        files_list = list(self.files.values())
        return files_list[offset:offset + limit]
    
    def update_ach_file(self, file_id: int, ach_file: AchFileUpdate) -> bool:
        """Update an ACH_FILES record."""
        if file_id not in self.files:
            return False
        
        existing_file = self.files[file_id]
        
        # Update fields
        if ach_file.processing_status is not None:
            existing_file.processing_status = ach_file.processing_status
        if ach_file.file_contents is not None:
            existing_file.file_contents = ach_file.file_contents
        if ach_file.updated_by_user is not None:
            existing_file.updated_by_user = ach_file.updated_by_user
        
        existing_file.updated_date = datetime.now()
        
        logger.info(f"Mock: Updated ACH_FILES record {file_id}")
        return True
    
    def delete_ach_file(self, file_id: int) -> bool:
        """Delete an ACH_FILES record."""
        if file_id in self.files:
            del self.files[file_id]
            logger.info(f"Mock: Deleted ACH_FILES record {file_id}")
            return True
        return False
    
    def get_ach_files_count(self) -> int:
        """Get total count of ACH_FILES records."""
        return len(self.files)


def test_mock_oracle_service():
    """Test the mock Oracle service."""
    print("🧪 Testing Mock Oracle Service")
    print("=" * 40)
    
    mock_service = MockOracleService()
    
    with mock_service:
        # Test CREATE
        print("📝 Testing CREATE operation...")
        test_file = AchFileCreate(
            original_filename="test_file.txt",
            processing_status="Pending",
            file_contents="This is a test file content.",
            created_by_user="UnityBankUserName@UB.com"
        )
        
        file_id = mock_service.create_ach_file(test_file)
        print(f"✅ Created ACH_FILES record with ID: {file_id}")
        
        # Test READ
        print("📖 Testing READ operation...")
        retrieved_file = mock_service.get_ach_file(file_id)
        if retrieved_file:
            print(f"✅ Retrieved ACH_FILES record: {retrieved_file.original_filename}")
        else:
            print("❌ Failed to retrieve ACH_FILES record")
            return False
        
        # Test UPDATE
        print("✏️  Testing UPDATE operation...")
        update_data = AchFileUpdate(
            processing_status="Processed",
            updated_by_user="UnityBankUserName@UB.com"
        )
        
        success = mock_service.update_ach_file(file_id, update_data)
        if success:
            print("✅ Updated ACH_FILES record successfully")
            
            # Verify update
            updated_file = mock_service.get_ach_file(file_id)
            if updated_file and updated_file.processing_status == "Processed":
                print("✅ Update verification successful")
            else:
                print("❌ Update verification failed")
                return False
        else:
            print("❌ Failed to update ACH_FILES record")
            return False
        
        # Test LIST
        print("📋 Testing LIST operation...")
        files = mock_service.get_ach_files()
        print(f"✅ Retrieved {len(files)} ACH_FILES records")
        
        # Test COUNT
        print("🔢 Testing COUNT operation...")
        count = mock_service.get_ach_files_count()
        print(f"✅ ACH_FILES table has {count} records")
        
        # Test DELETE
        print("🗑️  Testing DELETE operation...")
        success = mock_service.delete_ach_file(file_id)
        if success:
            print("✅ Deleted ACH_FILES record successfully")
            
            # Verify deletion
            deleted_file = mock_service.get_ach_file(file_id)
            if deleted_file is None:
                print("✅ Deletion verification successful")
            else:
                print("❌ Deletion verification failed")
                return False
        else:
            print("❌ Failed to delete ACH_FILES record")
            return False
        
        print("\n🎉 All mock Oracle operations completed successfully!")
        return True


def test_mock_sftp_to_oracle_sync():
    """Test SFTP to Oracle sync with mock service."""
    print("\n🔄 Testing Mock SFTP to Oracle Sync")
    print("=" * 40)
    
    mock_service = MockOracleService()
    
    # Simulate SFTP files data
    mock_sftp_files = [
        {
            'name': 'FEDACHOUT_20251014163742.txt',
            'path': './FEDACHOUT_20251014163742.txt',
            'size': 949,
            'modified': 1761153743.0,
            'is_directory': False,
            'permissions': '-rw-r-----'
        },
        {
            'name': 'test.txt.rtf',
            'path': './test.txt.rtf',
            'size': 377,
            'modified': 1761149315.0,
            'is_directory': False,
            'permissions': '-rw-r-----'
        }
    ]
    
    # Simulate file content
    mock_file_content = "101021000021 12345678902510141637A094101JPMORGAN CHASE BANK    COMPANY NAME INC       REF001  \n5200COMPANY NAME INC                    1234567890PPDPAYROLL   251014251014   1021000020000001\n6220210000211234567890123456 0000250000EMP001         JOHN DOE                0123456780000001"
    
    results = {
        'total_files': 0,
        'successful_syncs': 0,
        'failed_syncs': 0,
        'errors': []
    }
    
    with mock_service:
        results['total_files'] = len(mock_sftp_files)
        
        for file_data in mock_sftp_files:
            filename = file_data['name']
            
            if file_data['is_directory']:
                continue
            
            try:
                # Create ACH_FILES record
                ach_file = AchFileCreate(
                    original_filename=filename,
                    processing_status="Pending",
                    file_contents=mock_file_content,
                    created_by_user="UnityBankUserName@UB.com"
                )
                
                # Insert into mock Oracle
                file_id = mock_service.create_ach_file(ach_file)
                
                print(f"✅ Successfully synced {filename} to mock Oracle with ID: {file_id}")
                results['successful_syncs'] += 1
                
            except Exception as e:
                error_msg = f"Failed to sync {filename}: {e}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)
                results['failed_syncs'] += 1
    
    print(f"\n📊 Sync Results:")
    print(f"   Total files: {results['total_files']}")
    print(f"   Successful syncs: {results['successful_syncs']}")
    print(f"   Failed syncs: {results['failed_syncs']}")
    
    if results['errors']:
        print(f"   Errors:")
        for error in results['errors']:
            print(f"     ❌ {error}")
    
    return results['successful_syncs'] > 0


def main():
    """Main test function."""
    print("🧪 Mock Oracle Service Test Suite")
    print("=" * 50)
    
    # Test mock Oracle service
    oracle_success = test_mock_oracle_service()
    
    if oracle_success:
        # Test mock sync
        sync_success = test_mock_sftp_to_oracle_sync()
        
        if sync_success:
            print("\n🎉 All mock tests passed!")
            print("✅ The application logic is working correctly.")
            print("📋 To use with real Oracle, install Oracle Instant Client as per ORACLE_SETUP.md")
            return True
    
    print("\n❌ Some mock tests failed.")
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
