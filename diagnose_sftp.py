#!/usr/bin/env python3
"""Comprehensive SFTP connection diagnostic for Azure Storage."""

import socket
import paramiko
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from obs_sftp_file_processor.config import config

def test_network_connectivity():
    """Test basic network connectivity to the SFTP server."""
    print("🌐 Testing Network Connectivity")
    print("=" * 40)
    
    host = config.sftp.host
    port = config.sftp.port
    
    try:
        print(f"Testing connection to {host}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print("✅ Network connectivity: SUCCESS")
            return True
        else:
            print(f"❌ Network connectivity: FAILED (Error code: {result})")
            return False
    except Exception as e:
        print(f"❌ Network connectivity: FAILED ({e})")
        return False

def test_ssh_banner():
    """Test SSH banner retrieval."""
    print("\n🔍 Testing SSH Banner")
    print("=" * 40)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((config.sftp.host, config.sftp.port))
        
        # Read SSH banner
        banner = sock.recv(1024).decode('utf-8', errors='ignore')
        print(f"SSH Banner: {banner.strip()}")
        
        sock.close()
        print("✅ SSH banner retrieved successfully")
        return True
    except Exception as e:
        print(f"❌ SSH banner test failed: {e}")
        return False

def test_authentication_methods():
    """Test different authentication methods."""
    print("\n🔐 Testing Authentication Methods")
    print("=" * 40)
    
    # Test different username formats
    username_variants = [
        config.sftp.username,  # Current format
        "obssftpuser",  # Just the username
        f"{config.sftp.host.split('.')[0]}.obssftpuser",  # Storage account + username
    ]
    
    for username in username_variants:
        print(f"\nTesting username: {username}")
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Try to connect with timeout
            client.connect(
                hostname=config.sftp.host,
                port=config.sftp.port,
                username=username,
                password=config.sftp.password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            
            print(f"✅ Authentication SUCCESS with username: {username}")
            client.close()
            return True
            
        except paramiko.AuthenticationException as e:
            print(f"❌ Authentication failed: {e}")
        except paramiko.SSHException as e:
            print(f"❌ SSH error: {e}")
        except Exception as e:
            print(f"❌ Connection error: {e}")
    
    return False

def test_sftp_capabilities():
    """Test SFTP-specific capabilities."""
    print("\n📁 Testing SFTP Capabilities")
    print("=" * 40)
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Use the working username format if we found one
        username = "obssftpazstoragesftp.obssftpuser"  # Try the current format
        
        client.connect(
            hostname=config.sftp.host,
            port=config.sftp.port,
            username=username,
            password=config.sftp.password,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        
        # Test SFTP
        sftp = client.open_sftp()
        print("✅ SFTP connection established")
        
        # List directory
        try:
            files = sftp.listdir(".")
            print(f"✅ Directory listing successful: {len(files)} items")
            for file in files[:5]:  # Show first 5 files
                print(f"   📄 {file}")
            if len(files) > 5:
                print(f"   ... and {len(files) - 5} more files")
        except Exception as e:
            print(f"❌ Directory listing failed: {e}")
        
        sftp.close()
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ SFTP capabilities test failed: {e}")
        return False

def main():
    """Run comprehensive SFTP diagnostics."""
    print("🔧 Azure Storage SFTP Diagnostic Tool")
    print("=" * 50)
    print(f"Target: {config.sftp.host}:{config.sftp.port}")
    print(f"Username: {config.sftp.username}")
    print(f"Password: {'*' * len(config.sftp.password) if config.sftp.password else 'None'}")
    print()
    
    # Run tests
    network_ok = test_network_connectivity()
    banner_ok = test_ssh_banner()
    auth_ok = test_authentication_methods()
    sftp_ok = test_sftp_capabilities()
    
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    print(f"Network Connectivity: {'✅ PASS' if network_ok else '❌ FAIL'}")
    print(f"SSH Banner: {'✅ PASS' if banner_ok else '❌ FAIL'}")
    print(f"Authentication: {'✅ PASS' if auth_ok else '❌ FAIL'}")
    print(f"SFTP Operations: {'✅ PASS' if sftp_ok else '❌ FAIL'}")
    
    if all([network_ok, banner_ok, auth_ok, sftp_ok]):
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Your Azure Storage SFTP connection is working correctly")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\n🔧 Troubleshooting suggestions:")
        
        if not network_ok:
            print("   - Check if the Azure Storage account exists")
            print("   - Verify the SFTP endpoint is enabled")
            print("   - Check firewall/network settings")
        
        if not auth_ok:
            print("   - Verify the username format (try different combinations)")
            print("   - Check if the password is correct")
            print("   - Ensure the user has SFTP permissions")
        
        if not sftp_ok:
            print("   - Check if SFTP is properly configured on Azure Storage")
            print("   - Verify the user has read permissions")

if __name__ == "__main__":
    main()
