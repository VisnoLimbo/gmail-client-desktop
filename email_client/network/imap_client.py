"""
High-level IMAP client wrapper.

This module provides a clean, high-level interface for IMAP operations,
hiding the complexity of imaplib and providing better error handling.
"""
import imaplib
import email
import re
import base64
from email.header import decode_header
from email.utils import parseaddr, parsedate_tz, mktime_tz
from typing import List, Optional, Tuple
from datetime import datetime
from email_client.models import EmailAccount, Folder, EmailMessage
from email_client.auth.oauth import TokenBundle
from email_client.config import DEFAULT_IMAP_PORT


class ImapError(Exception):
    """Base exception for IMAP-related errors."""
    pass


class ImapConnectionError(ImapError):
    """Raised when IMAP connection fails."""
    pass


class ImapAuthenticationError(ImapError):
    """Raised when IMAP authentication fails."""
    pass


class ImapOperationError(ImapError):
    """Raised when an IMAP operation fails."""
    pass


class ImapClient:
    """
    High-level IMAP client wrapper.
    
    Supports XOAUTH2 authentication and provides a clean interface
    for common IMAP operations.
    """
    
    def __init__(self, account: EmailAccount, token_bundle: Optional[TokenBundle] = None, password: Optional[str] = None):
        """
        Initialize the IMAP client.
        
        Args:
            account: The email account configuration.
            token_bundle: Optional OAuth token bundle for XOAUTH2 authentication.
            password: Optional password for password-based authentication.
        """
        self.account = account
        self.token_bundle = token_bundle
        self.password = password
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self._authenticated = False
    
    def _build_xoauth2_bytes(self) -> bytes:
        """
        Build the XOAUTH2 authentication string as raw bytes (for IMAP responder).
        
        Format: user=email\x01auth=Bearer access_token\x01\x01
        
        Returns:
            Raw bytes of the XOAUTH2 string (NOT base64-encoded).
            imaplib.authenticate() will automatically base64-encode this.
        """
        if not self.token_bundle or not self.token_bundle.access_token:
            raise ImapAuthenticationError("No access token available for XOAUTH2")
        
        # Check if token is expired and needs refresh
        from datetime import datetime, timezone
        now = datetime.now()
        
        if self.token_bundle.expires_at:
            # Check if token is expired based on stored expiration
            time_until_expiry = (self.token_bundle.expires_at - now).total_seconds()
            
            if time_until_expiry <= 0:
                print(f"❌ IMAP: Access token is EXPIRED! (expired {abs(time_until_expiry):.0f}s ago)")
                raise ImapAuthenticationError(
                    "OAuth access token has expired. Please remove and re-add your account to get a new token."
                )
            elif time_until_expiry < 300:  # Less than 5 minutes remaining
                print(f"⚠️  IMAP: Token expires soon ({time_until_expiry:.0f}s remaining)")
        else:
            print(f"⚠️  IMAP: Token has no expiration time stored!")
        
        # Strip whitespace from email to prevent XOAUTH2 authentication failures
        # Hidden whitespace in email address causes "Invalid SASL argument" errors
        email = self.account.email_address.strip()
        
        # Debug: Check for hidden whitespace and show exact email being used
        print(f"[DEBUG] Raw user email repr: {repr(self.account.email_address)}")
        print(f"[DEBUG] Using email in XOAUTH2: {repr(email)}")
        print(f"[DEBUG] Email length: {len(email)} chars")
        
        # Verify email doesn't have any hidden characters
        if email != self.account.email_address:
            print(f"⚠️  WARNING: Email had whitespace! Original: {repr(self.account.email_address)}, Stripped: {repr(email)}")
        
        # Additional verification: check for any non-ASCII or control characters
        if any(ord(c) < 32 or ord(c) > 126 for c in email if c not in '@.'):
            print(f"⚠️  WARNING: Email contains non-printable characters!")
            print(f"[DEBUG] Email bytes: {email.encode('utf-8')}")
        
        # Verify email format
        if '@' not in email or '.' not in email.split('@')[-1]:
            print(f"⚠️  WARNING: Email format looks invalid: {repr(email)}")
        
        # Build XOAUTH2 string - email MUST match exactly what token was issued for
        # Format: user=email\x01auth=Bearer token\x01\x01
        auth_string = f"user={email}\x01auth=Bearer {self.token_bundle.access_token}\x01\x01"
        
        # Debug: Verify structure and separators
        print(f"[DEBUG] XOAUTH2 auth_string length: {len(auth_string)} chars")
        # Check for \x01 separator correctly (it's a byte, so check in bytes)
        has_separator = b'\x01' in auth_string.encode('utf-8')
        print(f"[DEBUG] XOAUTH2 contains \\x01 separators: {has_separator}")
        print(f"[DEBUG] XOAUTH2 byte representation (first 100 bytes): {auth_string.encode('utf-8')[:100]}")
        
        # Show structure breakdown
        parts = auth_string.split('\x01')
        print(f"[DEBUG] XOAUTH2 structure: {len(parts)} parts after split by \\x01")
        if len(parts) != 4:
            print(f"⚠️  WARNING: Expected 4 parts (user=, auth=, \\x01, \\x01), got {len(parts)}!")
        else:
            print(f"[DEBUG] Part 1 (user): {parts[0]}")
            print(f"[DEBUG] Part 2 (auth): {parts[1][:50]}..." if len(parts[1]) > 50 else f"[DEBUG] Part 2 (auth): {parts[1]}")
        
        # Return raw bytes - imaplib will base64-encode it automatically
        auth_bytes = auth_string.encode('utf-8')
        print(f"[DEBUG] XOAUTH2 raw bytes length: {len(auth_bytes)} bytes (will be base64-encoded by imaplib)")
        
        return auth_bytes
    
    def _build_xoauth2_string(self) -> str:
        """
        Build the XOAUTH2 authentication string (base64-encoded, for SMTP compatibility).
        
        This method returns a base64-encoded string for SMTP usage.
        For IMAP, use _build_xoauth2_bytes() instead, as imaplib handles base64 encoding.
        
        Returns:
            Base64-encoded XOAUTH2 string.
        """
        # Get raw bytes and base64-encode them for SMTP usage
        auth_bytes = self._build_xoauth2_bytes()
        encoded = base64.b64encode(auth_bytes).decode('utf-8')
        print(f"[DEBUG] XOAUTH2 base64-encoded for SMTP: {len(encoded)} chars")
        return encoded
    
    def _connect(self) -> None:
        """Establish connection to IMAP server."""
        if self.connection and self._authenticated:
            return
        
        try:
            host = self.account.imap_host
            port = DEFAULT_IMAP_PORT
            
            # Connect with SSL
            self.connection = imaplib.IMAP4_SSL(host, port)
            
            # Authenticate
            if self.token_bundle:
                # Validate token bundle before using
                if not self.token_bundle.access_token:
                    raise ImapAuthenticationError(
                        "Token bundle exists but access_token is missing or empty. "
                        "The token may not have been saved correctly."
                    )
                
                # Use XOAUTH2 authentication for OAuth accounts
                print(f"🔐 Authenticating IMAP with XOAUTH2 for {self.account.email_address}...")
                
                # Pre-validate token with Google before attempting IMAP auth
                try:
                    import requests
                    token_info = requests.get(
                        'https://www.googleapis.com/oauth2/v1/tokeninfo',
                        params={'access_token': self.token_bundle.access_token},
                        timeout=5
                    ).json()
                    
                    if 'error' in token_info:
                        raise ImapAuthenticationError(
                            f"Token validation failed: {token_info.get('error')}. "
                            f"Please remove and re-add your account."
                        )
                    
                    token_email = token_info.get('email', '').strip()
                    token_scopes = token_info.get('scope', '').split() if token_info.get('scope') else []
                    has_imap_scope = 'https://mail.google.com/' in token_scopes
                    expires_in = token_info.get('expires_in', 0)
                    
                    account_email_stripped = self.account.email_address.strip()
                    emails_match = token_email.lower() == account_email_stripped.lower()
                    
                    print(f"[DEBUG] Pre-auth token check:")
                    print(f"  Token email: {repr(token_email)}")
                    print(f"  Account email: {repr(account_email_stripped)}")
                    print(f"  Emails match (case-insensitive): {emails_match}")
                    if not emails_match:
                        print(f"  ⚠️  WARNING: Email mismatch detected!")
                        print(f"     Token email length: {len(token_email)}")
                        print(f"     Account email length: {len(account_email_stripped)}")
                        if token_email.lower() != account_email_stripped.lower():
                            print(f"     Different emails: '{token_email}' vs '{account_email_stripped}'")
                    print(f"  Has IMAP scope: {has_imap_scope}")
                    print(f"  Expires in: {expires_in}s")
                    
                    # Use the token email in XOAUTH2 if there's a mismatch (token email is authoritative)
                    if not emails_match:
                        print(f"  ⚠️  Using token email ({token_email}) instead of account email for XOAUTH2")
                        # We'll use the token email when building the XOAUTH2 string
                    
                    if not has_imap_scope:
                        raise ImapAuthenticationError(
                            "Token does not have https://mail.google.com/ scope. "
                            "Please remove and re-add your account."
                        )
                    
                    if expires_in <= 0:
                        raise ImapAuthenticationError(
                            f"Token is expired (expires_in: {expires_in}s). "
                            "Please remove and re-add your account."
                        )
                except requests.RequestException as e:
                    print(f"⚠️  Could not verify token with Google (network error): {e}")
                    # Continue anyway - maybe it's a network issue
                except Exception as e:
                    if isinstance(e, ImapAuthenticationError):
                        raise
                    print(f"⚠️  Token validation warning: {e}")
                
                # Build the raw XOAUTH2 bytes (NOT base64-encoded)
                # imaplib.authenticate() will automatically base64-encode the bytes we return
                xoauth2_bytes = self._build_xoauth2_bytes()
                
                # For XOAUTH2, the responder should return RAW BYTES (not base64-encoded)
                # imaplib will automatically base64-encode the bytes before sending to the server
                # The lambda receives a challenge (bytes) and returns bytes (or None to abort)
                challenge_error_info = {'scope': None, 'status': None, 'schemes': None}
                
                def xoauth2_responder(challenge):
                    # Handle challenge (if any)
                    if challenge:
                        # Challenge is always bytes according to imaplib documentation
                        try:
                            challenge_str = challenge.decode('utf-8')
                            print(f"🔍 IMAP challenge received: {challenge_str}")
                            
                            # Try to parse as JSON (Google sends error responses as JSON)
                            import json
                            try:
                                challenge_data = json.loads(challenge_str)
                                if isinstance(challenge_data, dict):
                                    status = challenge_data.get('status')
                                    scope = challenge_data.get('scope', '')
                                    schemes = challenge_data.get('schemes', '')
                                    
                                    # Store error info for better error message later
                                    challenge_error_info['status'] = status
                                    challenge_error_info['scope'] = scope
                                    challenge_error_info['schemes'] = schemes
                                    
                                    print(f"🔍 Challenge details: status={status}, scope={scope}, schemes={schemes}")
                                    
                                    if status == '400' or status == '401':
                                        # Return None to abort authentication (imaplib will send '*')
                                        return None
                            except json.JSONDecodeError:
                                # Not JSON, might be a normal challenge - continue and return XOAUTH2
                                pass
                        except Exception as e:
                            print(f"⚠️  Error parsing challenge: {e}")
                            pass
                    
                    # Return the RAW BYTES (imaplib will base64-encode automatically)
                    return xoauth2_bytes
                
                try:
                    result, data = self.connection.authenticate('XOAUTH2', xoauth2_responder)
                    if result != 'OK':
                        error_msg = data[0].decode('utf-8') if data and data[0] else 'Unknown error'
                        raise ImapAuthenticationError(
                            f"XOAUTH2 authentication failed: {error_msg}"
                        )
                    print(f"✅ IMAP authentication successful")
                except imaplib.IMAP4.error as imap_error:
                    error_msg = str(imap_error)
                    print(f"IMAP: IMAP4 error during authentication: {error_msg}")
                    
                    # Check if this is a scope-related error based on challenge response
                    enhanced_error = error_msg
                    if "Invalid SASL argument" in error_msg or "BAD" in error_msg:
                        scope = challenge_error_info.get('scope')
                        status = challenge_error_info.get('status')
                        schemes = challenge_error_info.get('schemes')
                        
                        if scope:
                            print(f"⚠️  Google IMAP challenge requested scope: {scope}")
                            print(f"⚠️  Challenge status: {status}, schemes: {schemes}")
                            enhanced_error = (
                                f"IMAP authentication failed.\n"
                                f"Google IMAP server challenge: status={status}, scope={scope}, schemes={schemes}\n"
                                f"Original error: {error_msg}\n\n"
                                f"This usually means:\n"
                                f"1. The token is expired (even if expiration looks correct)\n"
                                f"2. The token doesn't have the required scope\n"
                                f"3. The OAuth client isn't properly configured for IMAP\n\n"
                                f"Please remove and re-add your account to get a fresh token."
                            )
                        else:
                            enhanced_error = (
                                f"{error_msg}\n\n"
                                "This error typically means the OAuth token is missing the required scope for IMAP access. "
                                "For Gmail, the token must include 'https://mail.google.com/' scope. "
                                "Please remove and re-add your account to get a new token with the correct scopes."
                            )
                    
                    raise ImapAuthenticationError(f"IMAP authentication error: {enhanced_error}")
            elif self.password:
                # Use password-based authentication
                result, data = self.connection.login(self.account.email_address, self.password)
                if result != 'OK':
                    error_msg = data[0].decode('utf-8') if data and data[0] else 'Unknown error'
                    raise ImapAuthenticationError(
                        f"Password authentication failed: {error_msg}"
                    )
            else:
                # No authentication method provided
                raise ImapAuthenticationError(
                    "No authentication method provided. Either token_bundle (for OAuth) or password (for password-based) is required."
                )
            
            self._authenticated = True
        except imaplib.IMAP4.error as e:
            raise ImapConnectionError(f"IMAP connection failed: {str(e)}")
        except Exception as e:
            if isinstance(e, (ImapError, ImapConnectionError, ImapAuthenticationError)):
                raise
            raise ImapConnectionError(f"Failed to connect to IMAP server: {str(e)}")
    
    def _ensure_connected(self) -> None:
        """Ensure connection is established."""
        if not self._authenticated or not self.connection:
            self._connect()
    
    def _quote_folder_name(self, folder_path: str) -> str:
        """
        Quote IMAP folder name if it contains spaces or special characters.
        
        IMAP requires folder names with spaces or special characters to be quoted.
        For example: "Sent Mail" -> '"Sent Mail"', "[Gmail]/All Mail" -> '"[Gmail]/All Mail"'
        
        Args:
            folder_path: The folder path to quote.
            
        Returns:
            The quoted folder path if needed, or the original path.
        """
        if not folder_path:
            return folder_path
        
        # If already quoted, return as is
        if folder_path.startswith('"') and folder_path.endswith('"'):
            return folder_path
        
        # Check if folder name needs quoting (contains spaces or special characters)
        # Simple folders like "INBOX" don't need quoting
        needs_quoting = (
            ' ' in folder_path or
            '[' in folder_path or
            ']' in folder_path or
            '/' in folder_path and not folder_path.startswith('"')
        )
        
        if needs_quoting:
            # Escape any existing quotes and wrap in quotes
            escaped = folder_path.replace('"', '\\"')
            return f'"{escaped}"'
        
        return folder_path
    
    def __enter__(self):
        """Context manager entry."""
        self._connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
    
    def close(self) -> None:
        """Close the IMAP connection."""
        if self.connection and self._authenticated:
            try:
                self.connection.logout()
            except Exception:
                pass
            finally:
                self.connection = None
                self._authenticated = False
    
    def list_folders(self) -> List[Folder]:
        """
        List all folders on the server.
        
        Returns:
            A list of Folder objects with name and server_path populated.
            
        Raises:
            ImapOperationError: If the operation fails.
        """
        self._ensure_connected()
        
        try:
            result, data = self.connection.list()
            if result != 'OK':
                raise ImapOperationError(f"Failed to list folders: {result}")
            
            folders = []
            for folder_data in data:
                try:
                    folder = self._parse_folder_list_item(folder_data)
                    if folder:
                        folders.append(folder)
                except Exception as e:
                    # Skip folders that can't be parsed
                    continue
            
            return folders
        except ImapOperationError:
            raise
        except Exception as e:
            raise ImapOperationError(f"Error listing folders: {str(e)}")
    
    def _parse_folder_list_item(self, folder_data: bytes) -> Optional[Folder]:
        """
        Parse an IMAP LIST response item into a Folder object.
        
        Args:
            folder_data: Raw folder data from IMAP LIST command.
            
        Returns:
            A Folder object or None if parsing fails.
        """
        try:
            if isinstance(folder_data, bytes):
                folder_str = folder_data.decode('utf-8', errors='ignore')
            else:
                folder_str = str(folder_data)
            
            # IMAP LIST format: (flags) "hierarchy" "folder name"
            # Example: (\HasNoChildren) "/" "INBOX"
            
            # Extract folder path (last quoted string)
            quoted_strings = re.findall(r'"([^"]*)"', folder_str)
            if not quoted_strings:
                return None
            
            server_path = quoted_strings[-1]
            
            # Decode folder name if it's encoded
            try:
                decoded_parts = decode_header(server_path)
                decoded_path = ""
                for part, encoding in decoded_parts:
                    if isinstance(part, bytes):
                        if encoding:
                            decoded_path += part.decode(encoding)
                        else:
                            decoded_path += part.decode('utf-8', errors='ignore')
                    else:
                        decoded_path += part
                server_path = decoded_path
            except Exception:
                pass  # Use original if decoding fails
            
            # Extract folder name (last part of path)
            name = server_path.split('/')[-1] if '/' in server_path else server_path
            
            # Determine if it's a system folder
            path_upper = server_path.upper()
            is_system = (
                path_upper == 'INBOX' or
                'SENT' in path_upper or
                'DRAFT' in path_upper or
                'TRASH' in path_upper or
                'DELETED' in path_upper
            )
            
            return Folder(
                account_id=self.account.id or 0,
                name=name,
                server_path=server_path,
                is_system_folder=is_system,
                unread_count=0,  # Will be updated when fetching headers
            )
        except Exception:
            return None
    
    def fetch_headers(
        self,
        folder: Folder,
        limit: int = 100
    ) -> List[EmailMessage]:
        """
        Fetch email headers from a folder.
        
        Args:
            folder: The folder to fetch from.
            limit: Maximum number of emails to fetch.
            
        Returns:
            A list of EmailMessage objects with metadata and flags populated,
            but not body content.
            
        Raises:
            ImapOperationError: If the operation fails.
        """
        self._ensure_connected()
        
        try:
            # Select the folder (quote folder name if it contains spaces or special characters)
            folder_path = self._quote_folder_name(folder.server_path)
            result, data = self.connection.select(folder_path)
            if result != 'OK':
                raise ImapOperationError(f"Failed to select folder '{folder.server_path}': {result}")
            
            # Search for all messages
            result, message_ids = self.connection.search(None, 'ALL')
            if result != 'OK':
                raise ImapOperationError(f"Failed to search folder '{folder.server_path}': {result}")
            
            if not message_ids or not message_ids[0]:
                return []
            
            # Parse message IDs
            uid_list = message_ids[0].decode('utf-8').split()
            if not uid_list:
                return []
            
            # Get the most recent messages (limit)
            uid_list = uid_list[-limit:] if len(uid_list) > limit else uid_list
            
            if not uid_list:
                return []
            
            # Fetch headers and flags in batch (much faster than individual requests)
            # IMAP supports fetching multiple messages at once
            messages = self._fetch_message_headers_batch(uid_list, folder)
            
            # Reverse to get most recent first
            messages.reverse()
            
            return messages
        except ImapOperationError:
            raise
        except Exception as e:
            raise ImapOperationError(f"Error fetching headers: {str(e)}")
    
    def _fetch_message_headers_batch(self, uid_list: List[str], folder: Folder) -> List[EmailMessage]:
        """
        Fetch headers and flags for multiple messages in a single IMAP request.
        
        This is much faster than fetching messages one by one.
        
        Args:
            uid_list: List of UID strings to fetch.
            folder: The folder containing the messages.
            
        Returns:
            List of EmailMessage objects.
        """
        messages = []
        
        if not uid_list:
            return messages
        
        try:
            # Build UID range string for batch fetch
            # Format: "1,2,3" or "1:100" for ranges
            # For simplicity, we'll use comma-separated list
            uid_range = ','.join(uid_list)
            
            # Fetch headers and flags for all UIDs in one request
            result, data = self.connection.uid('fetch', uid_range, '(RFC822.HEADER FLAGS)')
            
            if result != 'OK':
                # If batch fetch fails, fall back to individual fetches
                print(f"Batch fetch failed with result: {result}, falling back to individual fetches")
                return self._fallback_individual_fetch(uid_list, folder)
            
            if not data:
                return messages
            
            # Parse all responses
            # IMAP can return data in different formats:
            # - List of tuples: [(b'1 (UID 123 FLAGS (\\Seen) RFC822.HEADER {1234}', b'headers...'), ...]
            # - List of bytes: [b'1 (UID 123 ...', b'headers...', b'2 (UID 124 ...', ...]
            # - Mixed format
            
            # Handle case where data is a list of tuples
            response_items = []
            if data and isinstance(data[0], tuple):
                response_items = data
            elif data:
                # Try to parse as alternating format
                # Sometimes IMAP returns: [b'1 (UID ...', b'headers', b'2 (UID ...', b'headers', ...]
                i = 0
                while i < len(data) - 1:
                    if isinstance(data[i], bytes) and isinstance(data[i+1], bytes):
                        response_items.append((data[i], data[i+1]))
                        i += 2
                    else:
                        i += 1
            
            for response_item in response_items:
                if not isinstance(response_item, tuple) or len(response_item) < 2:
                    continue
                
                try:
                    # Extract UID from first part (e.g., "1 (UID 123 FLAGS (\\Seen) RFC822.HEADER {1234}")
                    flags_str = str(response_item[0])
                    
                    # Extract UID from the response
                    uid_match = re.search(r'UID\s+(\d+)', flags_str)
                    if not uid_match:
                        continue
                    
                    uid = int(uid_match.group(1))
                    
                    # Extract flags
                    flags = self._parse_flags(flags_str)
                    
                    # Extract headers from second part
                    headers_bytes = response_item[1]
                    if not isinstance(headers_bytes, bytes):
                        continue
                    
                    # Parse email headers
                    msg = email.message_from_bytes(headers_bytes)
                    
                    # Extract metadata
                    subject = self._decode_header(msg.get('Subject', ''))
                    sender = self._decode_header(msg.get('From', ''))
                    recipients_str = self._decode_header(msg.get('To', ''))
                    
                    # Parse sender
                    sender_name, sender_email = parseaddr(sender)
                    if not sender_email:
                        sender_email = sender
                    
                    # Parse recipients
                    recipients = []
                    if recipients_str:
                        for addr in recipients_str.split(','):
                            _, email_addr = parseaddr(addr.strip())
                            if email_addr:
                                recipients.append(email_addr)
                    
                    # Parse dates
                    sent_at = self._parse_date(msg.get('Date'))
                    received_at = sent_at
                    
                    # Extract preview text (first line of body, but we only have headers)
                    preview_text = ""
                    
                    # Check for attachments
                    has_attachments = 'Content-Disposition' in msg or 'attachment' in str(msg.get('Content-Type', '')).lower()
                    
                    # Determine if read
                    is_read = '\\Seen' in flags
                    
                    message = EmailMessage(
                        account_id=self.account.id or 0,
                        folder_id=folder.id or 0,
                        uid_on_server=uid,
                        sender=sender_email,
                        recipients=recipients,
                        subject=subject,
                        preview_text=preview_text,
                        sent_at=sent_at,
                        received_at=received_at,
                        is_read=is_read,
                        has_attachments=has_attachments,
                        flags=flags,
                    )
                    messages.append(message)
                except Exception as e:
                    # Skip messages that can't be parsed
                    continue
            
            return messages
        except Exception as e:
            # If batch fetch fails, fall back to individual fetches
            print(f"Batch fetch exception: {e}, falling back to individual fetches")
            return self._fallback_individual_fetch(uid_list, folder)
    
    def _fallback_individual_fetch(self, uid_list: List[str], folder: Folder) -> List[EmailMessage]:
        """Fallback to individual fetches if batch fetch fails"""
        messages = []
        for uid_str in uid_list:
            try:
                uid = int(uid_str)
                message = self._fetch_message_headers(uid, folder)
                if message:
                    messages.append(message)
            except Exception:
                continue
        return messages
    
    def _fetch_message_headers(self, uid: int, folder: Folder) -> Optional[EmailMessage]:
        """
        Fetch headers and flags for a single message.
        
        Args:
            uid: The message UID.
            folder: The folder containing the message.
            
        Returns:
            An EmailMessage object with headers and flags populated.
        """
        try:
            # Fetch headers and flags
            result, data = self.connection.uid('fetch', str(uid), '(RFC822.HEADER FLAGS)')
            if result != 'OK' or not data or not data[0]:
                return None
            
            # Parse the response
            # data[0] is typically: (b'1 (UID 123 FLAGS (\\Seen \\Flagged) RFC822.HEADER {size}', b'headers...')
            response_item = data[0]
            if not isinstance(response_item, tuple) or len(response_item) < 2:
                return None
            
            # Extract flags from the first part
            flags_str = str(response_item[0])
            flags = self._parse_flags(flags_str)
            
            # Extract headers from the second part
            headers_bytes = response_item[1]
            if not isinstance(headers_bytes, bytes):
                return None
            
            # Parse email headers
            msg = email.message_from_bytes(headers_bytes)
            
            # Extract metadata
            subject = self._decode_header(msg.get('Subject', ''))
            sender = self._decode_header(msg.get('From', ''))
            recipients_str = self._decode_header(msg.get('To', ''))
            
            # Parse sender
            sender_name, sender_email = parseaddr(sender)
            if not sender_email:
                sender_email = sender
            
            # Parse recipients
            recipients = []
            if recipients_str:
                for addr in recipients_str.split(','):
                    _, email_addr = parseaddr(addr.strip())
                    if email_addr:
                        recipients.append(email_addr)
            
            # Parse dates
            sent_at = self._parse_date(msg.get('Date'))
            received_at = sent_at  # IMAP doesn't provide received_at separately
            
            # Extract preview text (first line of body, but we only have headers)
            preview_text = ""
            
            # Check for attachments
            has_attachments = 'Content-Disposition' in msg or 'attachment' in str(msg.get('Content-Type', '')).lower()
            
            # Determine if read
            is_read = '\\Seen' in flags
            
            return EmailMessage(
                account_id=self.account.id or 0,
                folder_id=folder.id or 0,
                uid_on_server=uid,
                sender=sender_email,
                recipients=recipients,
                subject=subject,
                preview_text=preview_text,
                sent_at=sent_at,
                received_at=received_at,
                is_read=is_read,
                has_attachments=has_attachments,
                flags=flags,
            )
        except Exception:
            return None
    
    def _parse_flags(self, flags_str: str) -> set:
        """Parse IMAP flags from a response string."""
        flags = set()
        # Look for flags like \Seen, \Flagged, etc.
        flag_pattern = r'\\([A-Za-z]+)'
        matches = re.findall(flag_pattern, flags_str)
        for match in matches:
            flags.add(f'\\{match}')
        return flags
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse an email date string to datetime."""
        if not date_str:
            return None
        try:
            date_tuple = parsedate_tz(date_str)
            if date_tuple:
                return datetime.fromtimestamp(mktime_tz(date_tuple))
        except Exception:
            pass
        return None
    
    def _decode_header(self, header: str) -> str:
        """Decode an email header."""
        try:
            decoded_parts = decode_header(header)
            decoded_str = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_str += part.decode(encoding)
                    else:
                        decoded_str += part.decode('utf-8', errors='ignore')
                else:
                    decoded_str += part
            return decoded_str
        except Exception:
            return header
    
    def fetch_body(
        self,
        folder: Folder,
        message_uid: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Fetch the body of an email message.
        
        Args:
            folder: The folder containing the message.
            message_uid: The message UID as a string.
            
        Returns:
            A tuple of (plain_text, html_text). Either or both may be None.
            
        Raises:
            ImapOperationError: If the operation fails.
        """
        self._ensure_connected()
        
        try:
            # Select the folder (quote folder name if it contains spaces or special characters)
            folder_path = self._quote_folder_name(folder.server_path)
            result, data = self.connection.select(folder_path)
            if result != 'OK':
                raise ImapOperationError(f"Failed to select folder '{folder.server_path}': {result}")
            
            # Fetch the message body
            result, data = self.connection.uid('fetch', message_uid, '(RFC822)')
            if result != 'OK' or not data or not data[0]:
                raise ImapOperationError(f"Failed to fetch message {message_uid}")
            
            # Parse the email
            response_item = data[0]
            if not isinstance(response_item, tuple) or len(response_item) < 2:
                raise ImapOperationError(f"Invalid response format for message {message_uid}")
            
            email_bytes = response_item[1]
            if not isinstance(email_bytes, bytes):
                raise ImapOperationError(f"Invalid email data for message {message_uid}")
            
            msg = email.message_from_bytes(email_bytes)
            
            # Extract body parts
            plain_text = None
            html_text = None
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    # Skip attachments
                    if "attachment" in content_disposition.lower():
                        continue
                    
                    if content_type == "text/plain" and plain_text is None:
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                plain_text = payload.decode('utf-8', errors='ignore')
                        except Exception:
                            pass
                    elif content_type == "text/html" and html_text is None:
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                html_text = payload.decode('utf-8', errors='ignore')
                        except Exception:
                            pass
            else:
                content_type = msg.get_content_type()
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        if content_type == "text/plain":
                            plain_text = payload.decode('utf-8', errors='ignore')
                        elif content_type == "text/html":
                            html_text = payload.decode('utf-8', errors='ignore')
                except Exception:
                    pass
            
            return (plain_text, html_text)
        except ImapOperationError:
            raise
        except Exception as e:
            raise ImapOperationError(f"Error fetching body: {str(e)}")
    
    def mark_read(self, folder: Folder, message_uid: str) -> None:
        """
        Mark a message as read.
        
        Args:
            folder: The folder containing the message.
            message_uid: The message UID as a string.
            
        Raises:
            ImapOperationError: If the operation fails.
        """
        self._ensure_connected()
        
        try:
            # Select the folder (quote folder name if it contains spaces or special characters)
            folder_path = self._quote_folder_name(folder.server_path)
            result, data = self.connection.select(folder_path)
            if result != 'OK':
                raise ImapOperationError(f"Failed to select folder '{folder.server_path}': {result}")
            
            # Add \Seen flag
            result, data = self.connection.uid('store', message_uid, '+FLAGS', '(\\Seen)')
            if result != 'OK':
                raise ImapOperationError(f"Failed to mark message {message_uid} as read: {result}")
        except ImapOperationError:
            raise
        except Exception as e:
            raise ImapOperationError(f"Error marking message as read: {str(e)}")
    
    def move_message(
        self,
        src: Folder,
        dest: Folder,
        message_uid: str
    ) -> None:
        """
        Move a message from one folder to another.
        
        Args:
            src: The source folder.
            dest: The destination folder.
            message_uid: The message UID as a string.
            
        Raises:
            ImapOperationError: If the operation fails.
        """
        self._ensure_connected()
        
        try:
            # Select the source folder (quote folder name if it contains spaces or special characters)
            src_path = self._quote_folder_name(src.server_path)
            result, data = self.connection.select(src_path)
            if result != 'OK':
                raise ImapOperationError(f"Failed to select source folder '{src.server_path}': {result}")
            
            # Copy the message to destination (quote destination folder name too)
            dest_path = self._quote_folder_name(dest.server_path)
            result, data = self.connection.uid('copy', message_uid, dest_path)
            if result != 'OK':
                raise ImapOperationError(
                    f"Failed to copy message {message_uid} to '{dest.server_path}': {result}"
                )
            
            # Mark as deleted in source folder
            result, data = self.connection.uid('store', message_uid, '+FLAGS', '(\\Deleted)')
            if result != 'OK':
                raise ImapOperationError(f"Failed to mark message {message_uid} as deleted: {result}")
            
            # Expunge to actually delete
            result, data = self.connection.expunge()
            if result != 'OK':
                raise ImapOperationError(f"Failed to expunge deleted messages: {result}")
        except ImapOperationError:
            raise
        except Exception as e:
            raise ImapOperationError(f"Error moving message: {str(e)}")

