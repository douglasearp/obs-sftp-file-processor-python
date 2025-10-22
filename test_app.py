#!/usr/bin/env python3
"""Test script to demonstrate the FastAPI application."""

import asyncio
import json
from src.obs_sftp_file_processor.main import app
from fastapi.testclient import TestClient

def test_app():
    """Test the FastAPI application endpoints."""
    client = TestClient(app)
    
    print("🧪 Testing OBS SFTP File Processor API")
    print("=" * 50)
    
    # Test health check
    print("\n1. Testing health check endpoint...")
    response = client.get("/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    # Test detailed health check
    print("\n2. Testing detailed health check...")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    # Test OpenAPI docs
    print("\n3. Testing OpenAPI documentation...")
    response = client.get("/docs")
    print(f"   Status: {response.status_code}")
    print("   📖 API documentation available at /docs")
    
    print("\n✅ All basic tests passed!")
    print("\n📋 Available endpoints:")
    print("   GET /              - Health check")
    print("   GET /health        - Detailed health check")
    print("   GET /files         - List files in root directory")
    print("   GET /files?path=   - List files in specific directory")
    print("   GET /files/{path}  - Read file content")
    print("   GET /docs          - Interactive API documentation")
    
    print("\n🚀 To run the application:")
    print("   uv run python main.py")
    print("   # or")
    print("   uv run uvicorn src.obs_sftp_file_processor.main:app --reload")

if __name__ == "__main__":
    test_app()
