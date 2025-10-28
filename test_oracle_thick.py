#!/usr/bin/env python3
"""Test Oracle connection with explicit thick mode initialization."""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import oracledb
from obs_sftp_file_processor.config import config


def test_oracle_thick_mode():
    """Test Oracle connection with thick mode."""
    print("🔍 Testing Oracle Database Connection (Thick Mode)...")
    
    try:
        # Set environment variables
        oracle_home = os.path.expanduser("~/oracle/instantclient_23_3")
        os.environ['ORACLE_HOME'] = oracle_home
        os.environ['DYLD_LIBRARY_PATH'] = f"{oracle_home}:{os.environ.get('DYLD_LIBRARY_PATH', '')}"
        
        print(f"   📁 Oracle Home: {oracle_home}")
        print(f"   📚 Library Path: {os.environ.get('DYLD_LIBRARY_PATH', 'Not set')}")
        
        # Initialize thick mode
        print("   🔧 Initializing thick mode...")
        try:
            oracledb.init_oracle_client(lib_dir=oracle_home)
            print("   ✅ Thick mode initialized successfully")
        except Exception as e:
            print(f"   ⚠️  Thick mode init failed: {e}")
            # Try without lib_dir
            try:
                oracledb.init_oracle_client()
                print("   ✅ Thick mode initialized without lib_dir")
            except Exception as e2:
                print(f"   ❌ Failed to initialize thick mode: {e2}")
                return False
        
        # Test connection
        print("   🔌 Testing connection...")
        connection = oracledb.connect(
            user=config.oracle.username,
            password=config.oracle.password,
            dsn=config.oracle.dsn
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM ACH_FILES")
        count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        print(f"   ✅ Oracle connection successful!")
        print(f"   📊 ACH_FILES table has {count} records")
        return True
        
    except Exception as e:
        print(f"   ❌ Oracle connection failed: {e}")
        return False


def test_oracle_client_info():
    """Test Oracle client information."""
    print("\n🔍 Oracle Client Information:")
    
    try:
        # Check if thick mode is available
        print(f"   📦 oracledb version: {oracledb.__version__}")
        
        # Try to get client info
        try:
            client_info = oracledb.clientversion()
            print(f"   🏷️  Client version: {client_info}")
        except Exception as e:
            print(f"   ⚠️  Could not get client version: {e}")
        
        # Check environment
        oracle_home = os.environ.get('ORACLE_HOME', 'Not set')
        print(f"   🏠 ORACLE_HOME: {oracle_home}")
        
        lib_path = os.environ.get('DYLD_LIBRARY_PATH', 'Not set')
        print(f"   📚 DYLD_LIBRARY_PATH: {lib_path}")
        
        # Check if libclntsh.dylib exists
        if oracle_home != 'Not set':
            lib_file = os.path.join(oracle_home, 'libclntsh.dylib')
            if os.path.exists(lib_file):
                print(f"   ✅ libclntsh.dylib found: {lib_file}")
            else:
                print(f"   ❌ libclntsh.dylib not found: {lib_file}")
        
    except Exception as e:
        print(f"   ❌ Error getting client info: {e}")


def main():
    """Main test function."""
    print("🧪 Oracle Thick Mode Test")
    print("=" * 40)
    
    test_oracle_client_info()
    
    success = test_oracle_thick_mode()
    
    if success:
        print("\n🎉 Oracle thick mode is working!")
        print("✅ You can now use the Oracle integration")
    else:
        print("\n❌ Oracle thick mode failed")
        print("📋 Troubleshooting steps:")
        print("1. Verify Oracle Instant Client installation")
        print("2. Check environment variables")
        print("3. Ensure network connectivity to Oracle server")
        print("4. Verify Oracle server encryption settings")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
