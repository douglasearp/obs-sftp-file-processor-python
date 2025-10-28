#!/usr/bin/env python3
"""Oracle connection test with different modes."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import oracledb
from obs_sftp_file_processor.config import config


def test_oracle_thin_mode():
    """Test Oracle connection in thin mode."""
    print("🔍 Testing Oracle Database Connection (Thin Mode)...")
    
    try:
        # Set thin mode explicitly
        oracledb.init_oracle_client(lib_dir=None)
        
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
        
        print(f"✅ Oracle connection successful!")
        print(f"   📊 ACH_FILES table has {count} records")
        return True
        
    except Exception as e:
        print(f"❌ Oracle connection failed: {e}")
        return False


def test_oracle_without_encryption():
    """Test Oracle connection without network encryption."""
    print("🔍 Testing Oracle Database Connection (No Encryption)...")
    
    try:
        # Try to connect without encryption
        connection = oracledb.connect(
            user=config.oracle.username,
            password=config.oracle.password,
            dsn=config.oracle.dsn,
            # Try to disable encryption
            config_dir=None,
            wallet_location=None
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM ACH_FILES")
        count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        print(f"✅ Oracle connection successful!")
        print(f"   📊 ACH_FILES table has {count} records")
        return True
        
    except Exception as e:
        print(f"❌ Oracle connection failed: {e}")
        return False


def main():
    """Test different Oracle connection modes."""
    print("🧪 Oracle Connection Test Suite")
    print("=" * 50)
    
    # Test thin mode
    thin_success = test_oracle_thin_mode()
    
    if not thin_success:
        print("\n" + "=" * 50)
        # Test without encryption
        no_encrypt_success = test_oracle_without_encryption()
        
        if not no_encrypt_success:
            print("\n❌ All connection attempts failed.")
            print("\n📋 To fix Oracle connection issues:")
            print("1. Install Oracle Instant Client:")
            print("   - Download from: https://www.oracle.com/database/technologies/instant-client/downloads.html")
            print("   - Extract to a directory (e.g., /opt/oracle/instantclient_21_8)")
            print("   - Set LD_LIBRARY_PATH: export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_8:$LD_LIBRARY_PATH")
            print("2. Or configure Oracle to allow unencrypted connections")
            print("3. Or use a different Oracle client configuration")
            return False
    
    print("\n✅ Oracle connection successful!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
