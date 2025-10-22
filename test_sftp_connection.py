#!/usr/bin/env python3
"""Test script to verify SFTP connection to Azure Storage."""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from obs_sftp_file_processor.config import config
from obs_sftp_file_processor.sftp_service import SFTPService
from loguru import logger

def test_sftp_connection():
    """Test SFTP connection and basic operations."""
    print("🔗 Testing SFTP Connection to Azure Storage")
    print("=" * 50)
    
    # Display connection details (masked password)
    print(f"Host: {config.sftp.host}")
    print(f"Port: {config.sftp.port}")
    print(f"Username: {config.sftp.username}")
    print(f"Password: {'*' * len(config.sftp.password) if config.sftp.password else 'None'}")
    print(f"Timeout: {config.sftp.timeout}s")
    print()
    
    try:
        # Test connection
        print("1. Testing SFTP connection...")
        with SFTPService(config.sftp) as sftp:
            print("   ✅ Connection established successfully!")
            
            # Test listing files in root directory
            print("\n2. Listing files in root directory...")
            try:
                files = sftp.list_files(".")
                print(f"   📁 Found {len(files)} items:")
                for file_info in files[:10]:  # Show first 10 items
                    file_type = "📁" if file_info['is_directory'] else "📄"
                    size_mb = file_info['size'] / (1024 * 1024) if file_info['size'] > 0 else 0
                    print(f"      {file_type} {file_info['name']} ({size_mb:.2f} MB)")
                
                if len(files) > 10:
                    print(f"      ... and {len(files) - 10} more items")
                    
            except Exception as e:
                print(f"   ❌ Error listing files: {e}")
                return False
            
            # Test reading a small text file if available
            print("\n3. Testing file reading...")
            text_files = [f for f in files if not f['is_directory'] and f['name'].endswith(('.txt', '.log', '.json', '.csv'))]
            
            if text_files:
                test_file = text_files[0]['name']
                print(f"   📖 Attempting to read: {test_file}")
                try:
                    content = sftp.read_file(test_file)
                    print(f"   ✅ Successfully read {len(content)} bytes")
                    print(f"   📄 Content preview (first 200 chars):")
                    preview = content.decode('utf-8', errors='ignore')[:200]
                    print(f"      {preview}...")
                except Exception as e:
                    print(f"   ❌ Error reading file: {e}")
            else:
                print("   ℹ️  No text files found to test reading")
            
            # Test file existence check
            print("\n4. Testing file existence check...")
            if files:
                test_file = files[0]['name']
                exists = sftp.file_exists(test_file)
                print(f"   📋 File '{test_file}' exists: {exists}")
            
            print("\n✅ All SFTP operations completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ SFTP connection failed: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("   - Verify the Azure Storage SFTP endpoint is accessible")
        print("   - Check if the credentials are correct")
        print("   - Ensure the SFTP service is enabled on your Azure Storage account")
        print("   - Verify network connectivity and firewall settings")
        return False

def test_fastapi_endpoints():
    """Test FastAPI endpoints with SFTP integration."""
    print("\n🌐 Testing FastAPI Endpoints")
    print("=" * 50)
    
    try:
        from fastapi.testclient import TestClient
        from obs_sftp_file_processor.main import app
        
        client = TestClient(app)
        
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = client.get("/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.text}")
            return False
        
        # Test files listing endpoint
        print("\n2. Testing files listing endpoint...")
        response = client.get("/files")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data['total_count']} items in {data['path']}")
            if data['files']:
                print("   📁 Sample files:")
                for file_info in data['files'][:5]:
                    file_type = "📁" if file_info['is_directory'] else "📄"
                    print(f"      {file_type} {file_info['name']}")
        else:
            print(f"   ❌ Files listing failed: {response.text}")
            return False
        
        print("\n✅ All FastAPI endpoints working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI testing failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Azure Storage SFTP Connection Test")
    print("=" * 60)
    
    # Test SFTP connection
    sftp_success = test_sftp_connection()
    
    # Test FastAPI endpoints
    api_success = test_fastapi_endpoints()
    
    print("\n" + "=" * 60)
    if sftp_success and api_success:
        print("🎉 SUCCESS: All tests passed!")
        print("✅ SFTP connection to Azure Storage is working")
        print("✅ FastAPI application is functional")
        print("\n🚀 You can now run the application with:")
        print("   uv run python main.py")
        print("   # or")
        print("   uv run uvicorn src.obs_sftp_file_processor.main:app --reload")
    else:
        print("❌ FAILURE: Some tests failed")
        if not sftp_success:
            print("❌ SFTP connection issues detected")
        if not api_success:
            print("❌ FastAPI endpoint issues detected")
        sys.exit(1)
