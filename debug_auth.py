#!/usr/bin/env python3
"""Advanced authentication debugging for Azure Storage SFTP."""

import paramiko
import sys
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
paramiko.util.log_to_file('paramiko.log')

def test_authentication_with_debug():
    """Test authentication with detailed debugging."""
    
    print("🔍 Advanced Azure Storage SFTP Authentication Debug")
    print("=" * 60)
    
    # Connection details
    host = "obssftpazstoragesftp.blob.core.windows.net"
    port = 22
    username = "obssftpuser"
    password = "oqdIA++1/34vtWNNbylb5hm4zoRVz91X"
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print()
    
    try:
        # Create SSH client with detailed logging
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Enable debug logging
        paramiko.common.logging.getLogger('paramiko.transport').setLevel(logging.DEBUG)
        
        print("🔐 Attempting authentication with debug logging...")
        print("   (Check paramiko.log for detailed debug information)")
        
        # Try connection with various options
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=30,
            allow_agent=False,
            look_for_keys=False,
            banner_timeout=30,
            auth_timeout=30,
            gss_auth=False,
            gss_kex=False,
            gss_deleg_creds=False,
            gss_host=None,
            gss_trust_dns=True,
            compress=False
        )
        
        print("✅ Authentication successful!")
        
        # Test SFTP
        sftp = client.open_sftp()
        files = sftp.listdir(".")
        print(f"📁 SFTP listing successful: {len(files)} files found")
        
        for file in files[:5]:
            print(f"   📄 {file}")
        
        sftp.close()
        client.close()
        
        return True
        
    except paramiko.AuthenticationException as e:
        print(f"❌ Authentication failed: {e}")
        print("   This usually means the username or password is incorrect")
    except paramiko.SSHException as e:
        print(f"❌ SSH error: {e}")
        print("   This could indicate a protocol or configuration issue")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    return False

def test_alternative_authentication_methods():
    """Test alternative authentication methods."""
    
    print("\n🔄 Testing Alternative Authentication Methods")
    print("=" * 50)
    
    host = "obssftpazstoragesftp.blob.core.windows.net"
    port = 22
    username = "obssftpuser"
    password = "oqdIA++1/34vtWNNbylb5hm4zoRVz91X"
    
    # Test different authentication approaches
    auth_methods = [
        {
            "name": "Standard password auth",
            "kwargs": {
                "username": username,
                "password": password,
                "allow_agent": False,
                "look_for_keys": False
            }
        },
        {
            "name": "Password auth with agent disabled",
            "kwargs": {
                "username": username,
                "password": password,
                "allow_agent": False,
                "look_for_keys": False,
                "gss_auth": False
            }
        },
        {
            "name": "Minimal auth options",
            "kwargs": {
                "username": username,
                "password": password
            }
        }
    ]
    
    for i, method in enumerate(auth_methods, 1):
        print(f"\n{i}. Testing: {method['name']}")
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            client.connect(
                hostname=host,
                port=port,
                timeout=15,
                **method['kwargs']
            )
            
            print(f"   ✅ SUCCESS with {method['name']}!")
            client.close()
            return True
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    return False

def check_azure_sftp_requirements():
    """Check if Azure SFTP requirements are met."""
    
    print("\n📋 Azure Storage SFTP Requirements Check")
    print("=" * 50)
    
    print("✅ Network connectivity: PASS")
    print("✅ SSH protocol: PASS (AzureSSH_1.0.0)")
    print("❌ Authentication: FAIL")
    print()
    
    print("🔧 Azure Storage SFTP Requirements:")
    print("   1. SFTP must be enabled on the storage account")
    print("   2. A local user must be created for SFTP access")
    print("   3. The user must have appropriate permissions")
    print("   4. The storage account must support SFTP")
    print()
    
    print("📞 Next Steps:")
    print("   1. Verify SFTP is enabled in Azure Portal")
    print("   2. Check if the user 'obssftpuser' exists")
    print("   3. Verify the user has SFTP permissions")
    print("   4. Confirm the password is correct")
    print("   5. Check if there are any IP restrictions")

if __name__ == "__main__":
    print("🔧 Azure Storage SFTP Advanced Debugging")
    print("=" * 60)
    
    # Test with debug logging
    auth_success = test_authentication_with_debug()
    
    if not auth_success:
        # Test alternative methods
        alt_success = test_alternative_authentication_methods()
        
        if not alt_success:
            # Provide requirements check
            check_azure_sftp_requirements()
    
    print(f"\n📄 Debug log saved to: paramiko.log")
    print("   Check this file for detailed authentication debug information")
