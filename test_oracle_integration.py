#!/usr/bin/env python3
"""Test Oracle database integration."""

import sys
import requests
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from obs_sftp_file_processor.config import config
from obs_sftp_file_processor.oracle_service import OracleService
from obs_sftp_file_processor.oracle_models import AchFileCreate, AchFileUpdate
from loguru import logger


def test_oracle_connection():
    """Test Oracle database connection."""
    print("🔍 Testing Oracle Database Connection...")
    
    try:
        oracle_service = OracleService(config.oracle)
        
        with oracle_service:
            # Test connection by getting count
            count = oracle_service.get_ach_files_count()
            print(f"✅ Oracle connection successful!")
            print(f"   📊 ACH_FILES table has {count} records")
            return True
            
    except Exception as e:
        print(f"❌ Oracle connection failed: {e}")
        return False


def test_oracle_crud_operations():
    """Test Oracle CRUD operations."""
    print("\n🔧 Testing Oracle CRUD Operations...")
    
    try:
        oracle_service = OracleService(config.oracle)
        
        with oracle_service:
            # Test CREATE
            print("   📝 Testing CREATE operation...")
            test_file = AchFileCreate(
                original_filename="test_file.txt",
                processing_status="Pending",
                file_contents="This is a test file content for Oracle testing.",
                created_by_user="UnityBankUserName@UB.com"
            )
            
            file_id = oracle_service.create_ach_file(test_file)
            print(f"   ✅ Created ACH_FILES record with ID: {file_id}")
            
            # Test READ
            print("   📖 Testing READ operation...")
            retrieved_file = oracle_service.get_ach_file(file_id)
            if retrieved_file:
                print(f"   ✅ Retrieved ACH_FILES record: {retrieved_file.original_filename}")
            else:
                print("   ❌ Failed to retrieve ACH_FILES record")
                return False
            
            # Test UPDATE
            print("   ✏️  Testing UPDATE operation...")
            update_data = AchFileUpdate(
                processing_status="Processed",
                updated_by_user="UnityBankUserName@UB.com"
            )
            
            success = oracle_service.update_ach_file(file_id, update_data)
            if success:
                print("   ✅ Updated ACH_FILES record successfully")
                
                # Verify update
                updated_file = oracle_service.get_ach_file(file_id)
                if updated_file and updated_file.processing_status == "Processed":
                    print("   ✅ Update verification successful")
                else:
                    print("   ❌ Update verification failed")
                    return False
            else:
                print("   ❌ Failed to update ACH_FILES record")
                return False
            
            # Test DELETE
            print("   🗑️  Testing DELETE operation...")
            success = oracle_service.delete_ach_file(file_id)
            if success:
                print("   ✅ Deleted ACH_FILES record successfully")
                
                # Verify deletion
                deleted_file = oracle_service.get_ach_file(file_id)
                if deleted_file is None:
                    print("   ✅ Deletion verification successful")
                else:
                    print("   ❌ Deletion verification failed")
                    return False
            else:
                print("   ❌ Failed to delete ACH_FILES record")
                return False
            
            print("   🎉 All CRUD operations completed successfully!")
            return True
            
    except Exception as e:
        print(f"   ❌ CRUD operations failed: {e}")
        return False


def test_fastapi_oracle_endpoints():
    """Test FastAPI Oracle endpoints."""
    print("\n🌐 Testing FastAPI Oracle Endpoints...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test health check
        print("   🔍 Testing API health...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("   ✅ API is healthy")
        else:
            print(f"   ❌ API health check failed: {response.status_code}")
            return False
        
        # Test Oracle endpoints
        print("   📊 Testing Oracle endpoints...")
        
        # Test GET /oracle/ach-files
        response = requests.get(f"{base_url}/oracle/ach-files")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ GET /oracle/ach-files successful - {data['total_count']} records")
        else:
            print(f"   ❌ GET /oracle/ach-files failed: {response.status_code}")
            return False
        
        # Test POST /oracle/ach-files
        test_data = {
            "original_filename": "api_test_file.txt",
            "processing_status": "Pending",
            "file_contents": "This is a test file created via API.",
            "created_by_user": "UnityBankUserName@UB.com"
        }
        
        response = requests.post(f"{base_url}/oracle/ach-files", json=test_data)
        if response.status_code == 200:
            created_file = response.json()
            file_id = created_file['file_id']
            print(f"   ✅ POST /oracle/ach-files successful - ID: {file_id}")
            
            # Test GET /oracle/ach-files/{id}
            response = requests.get(f"{base_url}/oracle/ach-files/{file_id}")
            if response.status_code == 200:
                print("   ✅ GET /oracle/ach-files/{id} successful")
            else:
                print(f"   ❌ GET /oracle/ach-files/{id} failed: {response.status_code}")
                return False
            
            # Test PUT /oracle/ach-files/{id}
            update_data = {
                "processing_status": "Processed",
                "updated_by_user": "UnityBankUserName@UB.com"
            }
            
            response = requests.put(f"{base_url}/oracle/ach-files/{file_id}", json=update_data)
            if response.status_code == 200:
                print("   ✅ PUT /oracle/ach-files/{id} successful")
            else:
                print(f"   ❌ PUT /oracle/ach-files/{id} failed: {response.status_code}")
                return False
            
            # Test DELETE /oracle/ach-files/{id}
            response = requests.delete(f"{base_url}/oracle/ach-files/{file_id}")
            if response.status_code == 200:
                print("   ✅ DELETE /oracle/ach-files/{id} successful")
            else:
                print(f"   ❌ DELETE /oracle/ach-files/{id} failed: {response.status_code}")
                return False
            
        else:
            print(f"   ❌ POST /oracle/ach-files failed: {response.status_code}")
            return False
        
        print("   🎉 All FastAPI Oracle endpoints working!")
        return True
        
    except Exception as e:
        print(f"   ❌ FastAPI Oracle endpoints test failed: {e}")
        return False


def test_sftp_to_oracle_sync():
    """Test SFTP to Oracle sync functionality."""
    print("\n🔄 Testing SFTP to Oracle Sync...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test sync endpoint
        response = requests.post(f"{base_url}/sync/sftp-to-oracle")
        if response.status_code == 200:
            results = response.json()
            print(f"   ✅ Sync completed successfully!")
            print(f"   📊 Results:")
            print(f"      Total files: {results['total_files']}")
            print(f"      Successful syncs: {results['successful_syncs']}")
            print(f"      Failed syncs: {results['failed_syncs']}")
            
            if results['errors']:
                print(f"      Errors:")
                for error in results['errors']:
                    print(f"        ❌ {error}")
            
            return results['successful_syncs'] > 0
            
        else:
            print(f"   ❌ Sync failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Sync test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🧪 Oracle Database Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Oracle Connection", test_oracle_connection),
        ("Oracle CRUD Operations", test_oracle_crud_operations),
        ("FastAPI Oracle Endpoints", test_fastapi_oracle_endpoints),
        ("SFTP to Oracle Sync", test_sftp_to_oracle_sync)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📋 Test Results Summary:")
    print("=" * 30)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Oracle integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
