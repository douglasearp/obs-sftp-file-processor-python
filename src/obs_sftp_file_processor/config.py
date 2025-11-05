"""Configuration management for SFTP settings."""

from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings
from .oracle_config import OracleConfig


class SFTPConfig(BaseSettings):
    """SFTP connection configuration."""
    
    # Previous SFTP Configuration (commented out)
    # host: str = Field("10.1.3.123", description="SFTP server hostname")
    # port: int = Field(22, description="SFTP server port")
    # username: str = Field("sftpuser1", description="SFTP username")
    # password: Optional[str] = Field("TheNextB1gSFTP##", description="SFTP password")
    
    # Current SFTP Configuration
    host: str = Field("10.1.3.123", description="SFTP server hostname")
    port: int = Field(2022, description="SFTP server port")
    username: str = Field("6001_obstest", description="SFTP username")
    password: Optional[str] = Field('OEL%7@71ov6I0@=V"`Tn', description="SFTP password")
    key_path: Optional[str] = Field(None, description="Path to SSH private key")
    timeout: int = Field(30, description="Connection timeout in seconds")
    
    model_config = ConfigDict(
        env_prefix="SFTP_",
        case_sensitive=False
    )


class AppConfig(BaseSettings):
    """Application configuration."""
    
    title: str = "OBS SFTP File Processor"
    version: str = "0.1.0"
    debug: bool = Field(False, description="Debug mode")
    log_level: str = Field("INFO", description="Logging level")
    
    # SFTP configuration
    sftp: SFTPConfig = Field(default_factory=SFTPConfig)
    
    # Oracle configuration
    oracle: OracleConfig = Field(default_factory=OracleConfig)
    
    model_config = ConfigDict(
        env_prefix="APP_",
        case_sensitive=False
    )


# Global configuration instance
config = AppConfig()
