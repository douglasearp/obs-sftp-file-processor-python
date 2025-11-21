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
        # Clean up any existing connection first
        self.disconnect()
        
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Authentication method
            auth_kwargs = {
                'hostname': self.config.host,
                'port': self.config.port,
                'username': self.config.username,
                'timeout': self.config.timeout,
                'allow_agent': False,  # Disable SSH agent
                'look_for_keys': False  # Don't look for keys in default locations
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
            
            # Set keepalive to prevent connection timeout
            transport = self.client.get_transport()
            if transport:
                transport.set_keepalive(30)  # Send keepalive every 30 seconds
            
            logger.info("SFTP connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to SFTP server: {e}")
            self.disconnect()
            raise
    
    def disconnect(self) -> None:
        """Close SFTP connection."""
        try:
            if self.sftp:
                try:
                    self.sftp.close()
                except:
                    pass
                self.sftp = None
        except:
            pass
        
        try:
            if self.client:
                try:
                    self.client.close()
                except:
                    pass
                self.client = None
        except:
            pass
        
        logger.debug("SFTP connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def _ensure_connected(self) -> None:
        """Ensure SFTP connection is active, reconnect if needed."""
        try:
            # Check if connection is still alive
            if self.sftp and self.client:
                # Check if transport is active
                transport = self.client.get_transport()
                if transport and transport.is_active():
                    # Connection appears active, but verify with a simple operation
                    try:
                        # Try to get current directory (lightweight operation)
                        self.sftp.getcwd()
                    except (paramiko.SSHException, EOFError, OSError, AttributeError):
                        # Connection is dead, reconnect
                        logger.warning("SFTP connection lost, reconnecting...")
                        self.disconnect()
                        self.connect()
                else:
                    # Transport not active, reconnect
                    logger.warning("SFTP transport not active, reconnecting...")
                    self.disconnect()
                    self.connect()
            elif not self.sftp or not self.client:
                # Not connected, establish connection
                logger.info("SFTP not connected, establishing connection...")
                self.connect()
        except Exception as e:
            logger.error(f"Failed to ensure SFTP connection: {e}")
            # Try to reconnect
            try:
                self.disconnect()
            except:
                pass
            self.connect()
    
    def list_files(self, remote_path: str = ".") -> List[Dict[str, Any]]:
        """List files in remote directory."""
        # Ensure connection is active before use
        self._ensure_connected()
        
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
            
        except (paramiko.SSHException, EOFError, OSError) as e:
            # Connection error, try to reconnect and retry once
            logger.warning(f"SFTP connection error during list_files: {e}, attempting reconnect...")
            try:
                self.disconnect()
                self.connect()
                # Retry the operation
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
                logger.info(f"Listed {len(files)} items from {remote_path} after reconnect")
                return files
            except Exception as retry_error:
                logger.error(f"Failed to list files in {remote_path} after reconnect: {retry_error}")
                raise
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
    
    def move_file(self, source_path: str, dest_path: str) -> None:
        """Move file from source_path to dest_path on SFTP server."""
        if not self.sftp:
            raise RuntimeError("SFTP connection not established")
        
        try:
            # Ensure destination directory exists
            dest_dir = str(Path(dest_path).parent)
            if dest_dir != "." and dest_dir != "/":
                self.ensure_directory_exists(dest_dir)
            
            # Move file (rename)
            self.sftp.rename(source_path, dest_path)
            logger.info(f"Moved file from {source_path} to {dest_path}")
            
        except Exception as e:
            logger.error(f"Failed to move file from {source_path} to {dest_path}: {e}")
            raise
    
    def ensure_directory_exists(self, remote_path: str) -> None:
        """Ensure directory exists on SFTP server, creating it if necessary."""
        if not self.sftp:
            raise RuntimeError("SFTP connection not established")
        
        try:
            # Check if directory exists
            try:
                self.sftp.stat(remote_path)
                # Directory exists
                return
            except FileNotFoundError:
                # Directory doesn't exist, create it
                # Create parent directories first if needed
                parent = str(Path(remote_path).parent)
                if parent != "." and parent != "/" and parent != remote_path:
                    self.ensure_directory_exists(parent)
                
                # Create the directory
                self.sftp.mkdir(remote_path)
                logger.info(f"Created directory: {remote_path}")
                
        except Exception as e:
            logger.error(f"Failed to ensure directory exists: {remote_path}: {e}")
            raise
