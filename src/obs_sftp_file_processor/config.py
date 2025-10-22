"""Configuration management for SFTP settings."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class SFTPConfig(BaseSettings):
    """SFTP connection configuration."""
    
    host: str = Field("obssftpazstoragesftp.container1.obssftpuser@obssftpazstoragesftp.blob.core.windows.net", description="SFTP server hostname")
    port: int = Field(22, description="SFTP server port")
    username: str = Field("obssftpuser", description="SFTP username")
    password: Optional[str] = Field("oqdIA++1/34vtWNNbylb5hm4zoRVz91X", description="SFTP password")
    key_path: Optional[str] = Field(None, description="Path to SSH private key")
    timeout: int = Field(30, description="Connection timeout in seconds")
    
    class Config:
        env_prefix = "SFTP_"
        case_sensitive = False


class AppConfig(BaseSettings):
    """Application configuration."""
    
    title: str = "OBS SFTP File Processor"
    version: str = "0.1.0"
    debug: bool = Field(False, description="Debug mode")
    log_level: str = Field("INFO", description="Logging level")
    
    # SFTP configuration
    sftp: SFTPConfig = Field(default_factory=SFTPConfig)
    
    class Config:
        env_prefix = "APP_"
        case_sensitive = False


# Global configuration instance
config = AppConfig()
