"""Test script to check SFTP permissions and working directory."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from obs_sftp_file_processor.config import config
from obs_sftp_file_processor.sftp_service import SFTPService

def test_sftp_permissions():
    """Test SFTP permissions and working directory."""
    try:
        sftp_service = SFTPService(config.sftp)
        
        print(f"\n{'='*60}")
        print(f"SFTP Permissions and Directory Test")
        print(f"{'='*60}")
        print(f"SFTP Server: {config.sftp.host}:{config.sftp.port}")
        print(f"SFTP Username: {config.sftp.username}")
        print(f"{'='*60}\n")
        
        with sftp_service:
            # Get current working directory
            try:
                cwd = sftp_service.sftp.getcwd()
                print(f"✅ Current Working Directory: {cwd}")
            except Exception as e:
                print(f"⚠️  Could not get current directory: {e}")
            
            # Check upload folder
            upload_folder = config.sftp.upload_folder
            print(f"\n📁 Checking Upload Folder: '{upload_folder}'")
            try:
                if sftp_service.file_exists(upload_folder):
                    info = sftp_service.get_file_info(upload_folder)
                    print(f"   ✅ EXISTS - Is Directory: {info['is_directory']}")
                    print(f"   Permissions: {info['permissions']}")
                else:
                    print(f"   ❌ Does NOT exist")
            except Exception as e:
                print(f"   ⚠️  Error checking: {e}")
            
            # Check archived folder
            archived_folder = config.sftp.archived_folder
            print(f"\n📁 Checking Archived Folder: '{archived_folder}'")
            try:
                if sftp_service.file_exists(archived_folder):
                    info = sftp_service.get_file_info(archived_folder)
                    print(f"   ✅ EXISTS - Is Directory: {info['is_directory']}")
                    print(f"   Permissions: {info['permissions']}")
                else:
                    print(f"   ❌ Does NOT exist")
                    print(f"\n   Attempting to create '{archived_folder}'...")
                    try:
                        sftp_service.ensure_directory_exists(archived_folder)
                        print(f"   ✅ SUCCESS: Created!")
                    except Exception as create_error:
                        print(f"   ❌ FAILED: {create_error}")
                        print(f"   Error type: {type(create_error).__name__}")
            except Exception as e:
                print(f"   ⚠️  Error checking: {e}")
            
            # List root directory to see what's accessible
            print(f"\n📋 Listing Root Directory Contents:")
            try:
                files = sftp_service.list_files(".")
                print(f"   Found {len(files)} items:")
                for item in files[:10]:  # Show first 10
                    item_type = "📁 DIR" if item['is_directory'] else "📄 FILE"
                    print(f"   {item_type} {item['name']} ({item['size']} bytes)")
                if len(files) > 10:
                    print(f"   ... and {len(files) - 10} more items")
            except Exception as e:
                print(f"   ⚠️  Could not list directory: {e}")
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_sftp_permissions()

