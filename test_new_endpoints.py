#!/usr/bin/env python3
"""Test the new file-by-name endpoints."""

import requests
import json

def test_endpoints():
    """Test all the new file-by-name endpoints."""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing New File-by-Name Endpoints")
    print("=" * 50)
    
    # Test 1: Get file by exact name
    print("\n1. Testing GET /file/{file_name} - Get file by exact name")
    print("   Testing: GET /file/test.txt.rtf")
    try:
        response = requests.get(f"{base_url}/file/test.txt.rtf")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ File found: {data['file_info']['name']}")
            print(f"   📄 Size: {data['file_info']['size']} bytes")
            print(f"   📝 Content type: {data['content_type']}")
            print(f"   🔤 Encoding: {data['encoding']}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 2: Search files by name pattern
    print("\n2. Testing GET /files/search/{file_name} - Search files by name pattern")
    print("   Testing: GET /files/search/test")
    try:
        response = requests.get(f"{base_url}/files/search/test")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data['total_count']} files matching 'test'")
            for file_info in data['files']:
                print(f"      📄 {file_info['name']} ({file_info['size']} bytes)")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 3: Search for non-existent file
    print("\n3. Testing search for non-existent file")
    print("   Testing: GET /files/search/nonexistent")
    try:
        response = requests.get(f"{base_url}/files/search/nonexistent")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found {data['total_count']} files matching 'nonexistent'")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 4: Get non-existent file by exact name
    print("\n4. Testing GET /file/{file_name} with non-existent file")
    print("   Testing: GET /file/nonexistent.txt")
    try:
        response = requests.get(f"{base_url}/file/nonexistent.txt")
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            print("   ✅ Correctly returned 404 for non-existent file")
        else:
            print(f"   ❌ Unexpected response: {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 5: List all available endpoints
    print("\n5. Available API Endpoints:")
    endpoints = [
        "GET / - Health check",
        "GET /health - Detailed health check", 
        "GET /files - List all files",
        "GET /files?path=/remote/path - List files in specific directory",
        "GET /files/{file_path} - Read file by path",
        "GET /file/{file_name} - Get file by exact name (NEW)",
        "GET /files/search/{file_name} - Search files by name pattern (NEW)",
        "GET /docs - Interactive API documentation"
    ]
    
    for endpoint in endpoints:
        print(f"   📍 {endpoint}")
    
    print("\n🎉 All endpoint tests completed!")

if __name__ == "__main__":
    test_endpoints()
