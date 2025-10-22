#!/usr/bin/env python3
"""Test different credential formats for Azure Storage SFTP."""

import paramiko
import sys

def test_credential_formats():
    """Test various credential format combinations."""
    
    # Azure Storage details
    storage_account = "obssftpazstoragesftp"
    username_part = "obssftpuser"
    password = "oqdIA++1/34vtWNNbylb5hm4zoRVz91X"
    host = "obssftpazstoragesftp.blob.core.windows.net"
    port = 22
    
    print("🔐 Testing Azure Storage SFTP Credential Formats")
    print("=" * 60)
    print(f"Storage Account: {storage_account}")
    print(f"Username Part: {username_part}")
    print(f"Password: {'*' * len(password)}")
    print(f"Host: {host}")
    print()
    
    # Different username formats to try
    username_formats = [
        username_part,  # Just the username
        f"{storage_account}.{username_part}",  # Storage account + username
        f"{storage_account}\\{username_part}",  # Storage account \ username
        f"{storage_account}/{username_part}",  # Storage account / username
        f"{username_part}@{storage_account}",  # Username @ storage account
    ]
    
    for i, username in enumerate(username_formats, 1):
        print(f"{i}. Testing username format: '{username}'")
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Try to connect
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=15,
                allow_agent=False,
                look_for_keys=False,
                banner_timeout=30,
                auth_timeout=30
            )
            
            print(f"   ✅ SUCCESS! Authentication worked with: '{username}'")
            
            # Test SFTP
            try:
                sftp = client.open_sftp()
                files = sftp.listdir(".")
                print(f"   📁 SFTP listing successful: {len(files)} files found")
                
                # Show first few files
                for file in files[:3]:
                    print(f"      📄 {file}")
                if len(files) > 3:
                    print(f"      ... and {len(files) - 3} more files")
                
                sftp.close()
                client.close()
                
                print(f"\n🎉 WORKING CREDENTIALS FOUND!")
                print(f"   Username: {username}")
                print(f"   Password: {'*' * len(password)}")
                print(f"   Host: {host}")
                print(f"   Port: {port}")
                
                return username
                
            except Exception as e:
                print(f"   ❌ SFTP test failed: {e}")
                client.close()
                
        except paramiko.AuthenticationException as e:
            print(f"   ❌ Authentication failed: {e}")
        except paramiko.SSHException as e:
            print(f"   ❌ SSH error: {e}")
        except Exception as e:
            print(f"   ❌ Connection error: {e}")
        
        print()
    
    print("❌ None of the credential formats worked")
    return None

def update_config_with_working_credentials(working_username):
    """Update the config file with working credentials."""
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
    working_username = test_credential_formats()
    
    if working_username:
        update_config_with_working_credentials(working_username)
        print(f"\n🚀 You can now test the application with:")
        print(f"   python test_sftp_connection.py")
    else:
        print(f"\n❌ No working credentials found.")
        print(f"Please verify:")
        print(f"   - The Azure Storage account name is correct")
        print(f"   - The username is correct")
        print(f"   - The password is correct")
        print(f"   - SFTP is enabled on the Azure Storage account")
        print(f"   - The user has proper permissions")
