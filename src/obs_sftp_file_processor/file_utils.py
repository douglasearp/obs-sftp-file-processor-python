"""Utility functions for file operations."""

from typing import Optional
from loguru import logger


def add_client_id_to_filename(filename: str, client_id: str) -> str:
    """
    Add client_id prefix to filename if not already present.
    
    Pattern: CLIENTID_{client_id}_{original_filename}
    
    Args:
        filename: Original filename
        client_id: Client ID to add to filename
        
    Returns:
        Filename with client_id prefix (if not already present)
    """
    # Check if client_id already in filename (case-insensitive)
    filename_upper = filename.upper()
    patterns = [
        f"CLIENTID_{client_id}_",
        f"CLIENTID_{client_id}-",
        f"CLIENTID_{client_id} ",
    ]
    
    for pattern in patterns:
        if pattern in filename_upper:
            logger.info(f"Filename already contains client_id pattern: {pattern}")
            return filename  # Already has client_id
    
    # Add client_id prefix
    new_filename = f"CLIENTID_{client_id}_{filename}"
    logger.info(f"Added client_id prefix: {filename} -> {new_filename}")
    return new_filename


def extract_client_id_from_filename(filename: str) -> Optional[str]:
    """
    Extract client_id from filename if present.
    
    Args:
        filename: Filename to check
        
    Returns:
        Client ID if found, None otherwise
    """
    filename_upper = filename.upper()
    
    # Check for CLIENTID_{client_id}_ pattern
    if filename_upper.startswith("CLIENTID_"):
        parts = filename_upper.split("_", 2)
        if len(parts) >= 2:
            return parts[1]
    
    return None

