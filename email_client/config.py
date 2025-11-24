"""
Global settings and constants for the email client.

This module provides configuration constants and helpers for the email client.
It is framework-agnostic and designed to be easily unit-testable.
"""
import os
from pathlib import Path
from typing import Optional


# Default port constants
DEFAULT_IMAP_PORT: int = 993
DEFAULT_SMTP_PORT: int = 587

# OAuth redirect URI (read from environment, with default)
OAUTH_REDIRECT_URI: str = "http://localhost:8080/callback"
# Database configuration
SQLITE_DB_PATH: Path = Path.home() / ".email_client" / "email_client.db"

# Sync and caching configuration
DEFAULT_REFRESH_INTERVAL_SECONDS: int = 60
MAX_CACHED_EMAILS_PER_FOLDER: int = 500


def load_env() -> None:
    """
    Load environment variables and apply sensible defaults.
    
    This function reads OAuth redirect URI from environment variables
    and sets up default paths. It should be called at application startup.
    
    Note: OAuth client credentials (GMAIL_CLIENT_ID, OUTLOOK_CLIENT_ID, etc.)
    are loaded from the root config.py module.
    """
    global OAUTH_REDIRECT_URI, SQLITE_DB_PATH
    
    # Load OAuth redirect URI from environment (if provided)
    oauth_redirect_uri = os.environ.get("OAUTH_REDIRECT_URI")
    if oauth_redirect_uri:
        OAUTH_REDIRECT_URI = oauth_redirect_uri
    
    # Allow override of database path via environment variable
    db_path_env = os.environ.get("SQLITE_DB_PATH")
    if db_path_env:
        SQLITE_DB_PATH = Path(db_path_env)
    
    # Ensure the database directory exists
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_database_url() -> str:
    """
    Get the SQLite database URL for database connections.
    
    Returns:
        A SQLite database URL string in the format 'sqlite:///path/to/database.db'
    
    Example:
        >>> get_database_url()
        'sqlite:///Users/username/.email_client/email_client.db'
    """
    # Convert Windows paths to forward slashes for SQLite URL
    db_path_str = str(SQLITE_DB_PATH).replace("\\", "/")
    return f"sqlite:///{db_path_str}"

