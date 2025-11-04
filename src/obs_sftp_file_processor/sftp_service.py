"""SFTP service for connecting to Azure Storage SFTP server."""

import os
import stat
from typing import List, Optional, Dict, Any
from pathlib import Path
import paramiko
from loguru import logger
from .config import SFTPConfig


class SFTPService:
    """Service for SFTP operations with Azure Storage."""
    
    def __init__(self, config: SFTPConfig):
        """Initialize SFTP service with configuration."""
        self.config = config
        self.client: Optional[paramiko.SSHClient] = None
        self.sftp: Optional[paramiko.SFTPClient] = None
    
    def connect(self) -> None:
        """Establish SFTP connection."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Authentication method
            auth_kwargs = {
                'hostname': self.config.host,
                'port': self.config.port,
                'username': self.config.username,
                'timeout': self.config.timeout
            }
            
            if self.config.key_path and os.path.exists(self.config.key_path):
                # Use SSH key authentication
                auth_kwargs['key_filename'] = self.config.key_path
                logger.info(f"Connecting to {self.config.host} using SSH key")
            elif self.config.password:
                # Use password authentication
                auth_kwargs['password'] = self.config.password
                logger.info(f"Connecting to {self.config.host} using password")
            else:
                raise ValueError("Either password or key_path must be provided")
            
            self.client.connect(**auth_kwargs)
            self.sftp = self.client.open_sftp()
            logger.info("SFTP connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to SFTP server: {e}")
            self.disconnect()
            raise
    
    def disconnect(self) -> None:
        """Close SFTP connection."""
        if self.sftp:
            self.sftp.close()
            self.sftp = None
        if self.client:
            self.client.close()
            self.client = None
        logger.info("SFTP connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def list_files(self, remote_path: str = ".") -> List[Dict[str, Any]]:
        """List files in remote directory."""
        if not self.sftp:
            raise RuntimeError("SFTP connection not established")
        
        try:
            files = []
            for item in self.sftp.listdir_attr(remote_path):
                file_info = {
                    'name': item.filename,
                    'size': item.st_size,
                    'modified': item.st_mtime,
                    'is_directory': stat.S_ISDIR(item.st_mode),
                    'permissions': stat.filemode(item.st_mode)
                }
                files.append(file_info)
            
            logger.info(f"Listed {len(files)} items from {remote_path}")
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files in {remote_path}: {e}")
            raise
    
    def read_file(self, remote_path: str) -> bytes:
        """Read file content from remote path."""
        if not self.sftp:
            raise RuntimeError("SFTP connection not established")
        
        try:
            with self.sftp.open(remote_path, 'rb') as remote_file:
                content = remote_file.read()
            
            logger.info(f"Read {len(content)} bytes from {remote_path}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to read file {remote_path}: {e}")
            raise
    
    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists on remote server."""
        if not self.sftp:
            raise RuntimeError("SFTP connection not established")
        
        try:
            self.sftp.stat(remote_path)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error checking file existence {remote_path}: {e}")
            raise
    
    def get_file_info(self, remote_path: str) -> Dict[str, Any]:
        """Get file information."""
        if not self.sftp:
            raise RuntimeError("SFTP connection not established")
        
        try:
            stat_info = self.sftp.stat(remote_path)
            return {
                'name': Path(remote_path).name,
                'path': remote_path,
                'size': stat_info.st_size,
                'modified': stat_info.st_mtime,
                'is_directory': stat.S_ISDIR(stat_info.st_mode),
                'permissions': stat.filemode(stat_info.st_mode)
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {remote_path}: {e}")
            raise
    
    def write_file(self, remote_path: str, content: bytes) -> None:
        """Write file content to remote path."""
        if not self.sftp:
            raise RuntimeError("SFTP connection not established")
        
        try:
            # Ensure parent directory exists
            remote_dir = str(Path(remote_path).parent)
            if remote_dir != "." and remote_dir != "/":
                try:
                    self.sftp.stat(remote_dir)
                except FileNotFoundError:
                    # Create directory if it doesn't exist
                    self.sftp.mkdir(remote_dir)
            
            # Write file content
            with self.sftp.open(remote_path, 'wb') as remote_file:
                remote_file.write(content)
            
            logger.info(f"Wrote {len(content)} bytes to {remote_path}")
            
        except Exception as e:
            logger.error(f"Failed to write file {remote_path}: {e}")
            raise
