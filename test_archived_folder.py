"""Test script to check if archived folder exists on SFTP server."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from obs_sftp_file_processor.config import config
from obs_sftp_file_processor.sftp_service import SFTPService
from loguru import logger

def test_archived_folder():
    """Test if archived folder exists on SFTP server."""
    try:
        sftp_service = SFTPService(config.sftp)
        
        print(f"\n{'='*60}")
        print(f"Testing SFTP Archived Folder")
        print(f"{'='*60}")
        print(f"SFTP Server: {config.sftp.host}:{config.sftp.port}")
        print(f"SFTP Username: {config.sftp.username}")
        print(f"Archived Folder Path: {config.sftp.archived_folder}")
        print(f"{'='*60}\n")
        
        with sftp_service:
            archived_folder = config.sftp.archived_folder
            
            # Check if folder exists
            try:
                # Try to get file info (will raise FileNotFoundError if doesn't exist)
                folder_info = sftp_service.get_file_info(archived_folder)
                
                if folder_info['is_directory']:
                    print(f"✅ SUCCESS: Archived folder '{archived_folder}' EXISTS")
                    print(f"   Path: {archived_folder}")
                    print(f"   Is Directory: {folder_info['is_directory']}")
                    print(f"   Permissions: {folder_info['permissions']}")
                    
                    # Try to list files in the folder
                    try:
                        files = sftp_service.list_files(archived_folder)
                        file_count = len([f for f in files if not f['is_directory']])
                        print(f"   Files in folder: {file_count}")
                        if file_count > 0:
                            print(f"   Sample files:")
                            for f in files[:5]:
                                if not f['is_directory']:
                                    print(f"     - {f['name']} ({f['size']} bytes)")
                    except Exception as e:
                        print(f"   ⚠️  Could not list files: {e}")
                else:
                    print(f"❌ ERROR: '{archived_folder}' exists but is NOT a directory")
                    
            except FileNotFoundError:
                print(f"❌ NOT FOUND: Archived folder '{archived_folder}' does NOT exist")
                print(f"\n   Attempting to create it...")
                
                try:
                    sftp_service.ensure_directory_exists(archived_folder)
                    print(f"✅ SUCCESS: Created archived folder '{archived_folder}'")
                    
                    # Verify it was created
                    folder_info = sftp_service.get_file_info(archived_folder)
                    if folder_info['is_directory']:
                        print(f"   Verified: Folder exists and is a directory")
                    else:
                        print(f"   ⚠️  Warning: Created but not recognized as directory")
                        
                except Exception as create_error:
                    print(f"❌ ERROR: Failed to create archived folder: {create_error}")
                    
            except Exception as e:
                print(f"❌ ERROR: Failed to check archived folder: {e}")
                print(f"   Error type: {type(e).__name__}")
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_archived_folder()

