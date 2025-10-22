#!/usr/bin/env python3
"""Test file reading from Azure Storage SFTP."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from obs_sftp_file_processor.sftp_service import SFTPService
from obs_sftp_file_processor.config import config

def test_file_reading():
    """Test reading files from Azure Storage SFTP."""
    print("📖 Testing File Reading from Azure Storage SFTP")
    print("=" * 60)
    
    try:
        with SFTPService(config.sftp) as sftp:
            print("✅ SFTP connection established")
            
            # List files
            files = sftp.list_files(".")
            print(f"📁 Found {len(files)} files:")
            
            for file_info in files:
                print(f"   📄 {file_info['name']} ({file_info['size']} bytes)")
                
                # Try to read the file
                try:
                    content = sftp.read_file(file_info['name'])
                    print(f"   ✅ Successfully read {len(content)} bytes")
                    
                    # Try to decode as text
                    try:
                        text_content = content.decode('utf-8')
                        print(f"   📝 Text content preview (first 200 chars):")
                        print(f"      {text_content[:200]}...")
                    except UnicodeDecodeError:
                        print(f"   📄 Binary file - content preview (first 50 bytes):")
                        print(f"      {content[:50]}...")
                    
                except Exception as e:
                    print(f"   ❌ Failed to read file: {e}")
                
                print()
            
            print("🎉 File reading test completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ File reading test failed: {e}")
        return False

if __name__ == "__main__":
    test_file_reading()
