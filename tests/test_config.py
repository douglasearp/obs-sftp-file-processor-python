"""Tests for configuration management."""

import pytest
from src.obs_sftp_file_processor.config import SFTPConfig, AppConfig


def test_sftp_config_defaults():
    """Test SFTP configuration defaults."""
    config = SFTPConfig()
    assert config.host == "obssftpazstoragesftp.container1.obssftpuser@obssftpazstoragesftp.blob.core.windows.net"
    assert config.port == 22
    assert config.username == "obssftpuser"
    assert config.password == "oqdIA++1/34vtWNNbylb5hm4zoRVz91X"
    assert config.timeout == 30


def test_app_config():
    """Test application configuration."""
    config = AppConfig()
    assert config.title == "OBS SFTP File Processor"
    assert config.version == "0.1.0"
    assert config.debug is False
    assert config.log_level == "INFO"
    assert isinstance(config.sftp, SFTPConfig)
