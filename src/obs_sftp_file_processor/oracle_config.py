"""Oracle database configuration."""

from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class OracleConfig(BaseSettings):
    """Oracle database connection configuration."""
    
    host: str = Field("10.1.0.111", description="Oracle database host")
    port: int = Field(1521, description="Oracle database port")
    service_name: str = Field("PDB_ACHDEV01.privatesubnet1.obsnetwork1.oraclevcn.com", description="Oracle service name")
    username: str = Field("achowner", description="Oracle username")
    password: str = Field("TLcbbhQuiV7##sLv4tMr", description="Oracle password")
    schema: str = Field("ACHOWNER", description="Oracle schema name")
    
    # Connection pool settings
    min_pool_size: int = Field(1, description="Minimum connection pool size")
    max_pool_size: int = Field(10, description="Maximum connection pool size")
    pool_increment: int = Field(1, description="Pool increment size")
    
    # Connection settings
    connect_timeout: int = Field(30, description="Connection timeout in seconds")
    read_timeout: int = Field(30, description="Read timeout in seconds")
    
    model_config = ConfigDict(
        env_prefix = "ORACLE_",
        case_sensitive = False
    )
    
    @property
    def connection_string(self) -> str:
        """Get Oracle connection string."""
        return f"{self.host}:{self.port}/{self.service_name}"
    
    @property
    def dsn(self) -> str:
        """Get Oracle DSN for oracledb."""
        return f"{self.host}:{self.port}/{self.service_name}"
