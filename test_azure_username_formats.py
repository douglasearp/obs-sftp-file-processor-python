#!/usr/bin/env python3
"""Test all possible Azure Storage SFTP username formats."""

import paramiko
import sys

def test_azure_username_formats():
    """Test various Azure Storage SFTP username formats."""
    
    print("🔍 Testing Azure Storage SFTP Username Formats")
    print("=" * 60)
    
    # Connection details
    host = "obssftpazstoragesftp.blob.core.windows.net"
    port = 22
    password = "oqdIA++1/34vtWNNbylb5hm4zoRVz91X"
    storage_account = "obssftpazstoragesftp"
    username_part = "obssftpuser"
    
    # All possible username formats for Azure Storage SFTP
    username_formats = [
        # Basic formats
        username_part,
        f"{storage_account}.{username_part}",
        f"{storage_account}\\{username_part}",
        f"{storage_account}/{username_part}",
        f"{username_part}@{storage_account}",
        
        # Azure-specific formats
        f"{storage_account}\\{username_part}",
        f"{storage_account}.{username_part}",
        f"{username_part}",
        
        # Alternative formats
        f"{username_part}@{storage_account}.blob.core.windows.net",
        f"{storage_account}.{username_part}@{storage_account}",
        f"{username_part}@{storage_account}.blob.core.windows.net",
        
        # Container-specific formats
        f"{storage_account}.container1.{username_part}",
        f"{username_part}@{storage_account}.container1",
        f"{storage_account}\\container1\\{username_part}",
        f"{storage_account}/container1/{username_part}",
    ]
    
    print(f"Testing {len(username_formats)} different username formats...")
    print(f"Host: {host}")
    print(f"Password: {'*' * len(password)}")
    print()
    
    for i, username in enumerate(username_formats, 1):
        print(f"{i:2d}. Testing: '{username}'")
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Try connection with timeout
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False,
                banner_timeout=15,
                auth_timeout=15
            )
            
            print(f"    ✅ SUCCESS! Username format: '{username}'")
            
            # Test SFTP
            try:
                sftp = client.open_sftp()
                files = sftp.listdir(".")
                print(f"    📁 SFTP listing: {len(files)} files found")
                
                # Show first few files
                for file in files[:3]:
                    print(f"       📄 {file}")
                if len(files) > 3:
                    print(f"       ... and {len(files) - 3} more files")
                
                sftp.close()
                client.close()
                
                print(f"\n🎉 WORKING CREDENTIALS FOUND!")
                print(f"   Username: {username}")
                print(f"   Password: {'*' * len(password)}")
                print(f"   Host: {host}")
                print(f"   Port: {port}")
                
                return username
                
            except Exception as e:
                print(f"    ❌ SFTP test failed: {e}")
                client.close()
                
        except paramiko.AuthenticationException as e:
            print(f"    ❌ Authentication failed: {e}")
        except paramiko.SSHException as e:
            print(f"    ❌ SSH error: {e}")
        except Exception as e:
            print(f"    ❌ Connection error: {e}")
        
        print()
    
    print("❌ None of the username formats worked")
    return None

def update_config_with_working_username(working_username):
    """Update the config file with the working username."""
    if not working_username:
        return
    
    print(f"\n🔧 Updating configuration with working username: {working_username}")
    
    # Read the current config file
    config_path = "src/obs_sftp_file_processor/config.py"
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Update the username field
    import re
    pattern = r'username: str = Field\("[^"]*", description="SFTP username"\)'
    replacement = f'username: str = Field("{working_username}", description="SFTP username")'
    updated_content = re.sub(pattern, replacement, content)
    
    # Write back to file
    with open(config_path, 'w') as f:
        f.write(updated_content)
    
    print(f"✅ Configuration updated successfully!")

if __name__ == "__main__":
    working_username = test_azure_username_formats()
    
    if working_username:
        update_config_with_working_username(working_username)
        print(f"\n🚀 You can now test the application with:")
        print(f"   python test_sftp_connection.py")
    else:
        print(f"\n❌ No working username format found.")
        print(f"\n🔧 Troubleshooting suggestions:")
        print(f"   1. Verify the Azure Storage account name is correct")
        print(f"   2. Check if SFTP is enabled on the storage account")
        print(f"   3. Verify the user 'obssftpuser' exists in Azure")
        print(f"   4. Check if the user has SFTP permissions")
        print(f"   5. Confirm the password is correct")
        print(f"   6. Check Azure documentation for the correct username format")
