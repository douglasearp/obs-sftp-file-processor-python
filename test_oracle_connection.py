#!/usr/bin/env python3
"""Simple Oracle connection test."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import oracledb
from obs_sftp_file_processor.config import config


def test_oracle_connection():
    """Test basic Oracle connection."""
    print("🔍 Testing Oracle Database Connection...")
    
    try:
        # Test basic connection
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


if __name__ == "__main__":
    test_oracle_connection()
