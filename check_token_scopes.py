#!/usr/bin/env python3
"""
Check what scopes are stored in the token for an account.
This helps verify if the token has the required IMAP scope.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from email_client.auth.accounts import get_accounts, get_token_bundle
    from email_client.storage.encryption import EncryptionManager
    from config import ENCRYPTION_KEY_FILE
    
    print("=" * 60)
    print("Token Scope Checker")
    print("=" * 60)
    print()
    
    # Get all accounts
    accounts = get_accounts()
    
    if not accounts:
        print("No accounts found in the database.")
        sys.exit(0)
    
    print(f"Found {len(accounts)} account(s):")
    print()
    
    for account in accounts:
        if account.auth_type != "oauth":
            print(f"Account: {account.email_address}")
            print(f"  Type: {account.auth_type} (not OAuth, skipping scope check)")
            print()
            continue
        
        print(f"Account: {account.email_address} (ID: {account.id})")
        
        try:
            # Try to get the raw encrypted token to check stored scopes
            import sqlite3
            from config import DB_PATH
            
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get the encrypted token bundle
            cursor.execute("SELECT encrypted_token_bundle FROM accounts WHERE id = ?", (account.id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row or not row["encrypted_token_bundle"]:
                print("  ✗ No token bundle found")
                print()
                continue
            
            # Decrypt and check
            encryption_manager = EncryptionManager()
            encrypted_data = row["encrypted_token_bundle"]
            
            try:
                decrypted_json = encryption_manager.decrypt(encrypted_data)
                token_data = json.loads(decrypted_json)
                
                # Check for scopes in stored data
                stored_scopes = token_data.get("scopes", [])
                
                if stored_scopes:
                    print(f"  Token scopes ({len(stored_scopes)}):")
                    has_imap_scope = "https://mail.google.com/" in stored_scopes
                    for scope in stored_scopes:
                        marker = "✓" if scope == "https://mail.google.com/" else " "
                        print(f"    {marker} {scope}")
                    
                    print()
                    if has_imap_scope:
                        print("  ✓ IMAP scope is present in token!")
                    else:
                        print("  ✗ IMAP scope is MISSING from token!")
                        print("  → You need to remove and re-add this account.")
                else:
                    print("  ⚠ Scopes not stored in token data")
                    print("  → This is expected if token was created before scope tracking was added.")
                    print("  → Remove and re-add the account to get a new token with scopes.")
                
                print()
                
            except Exception as e:
                print(f"  ✗ Error decrypting token: {e}")
                print()
        
        except Exception as e:
            print(f"  ✗ Error checking token: {e}")
            print()
    
    print("=" * 60)
    print()
    print("Note: If IMAP scope is missing, remove and re-add the account")
    print("      to get a new token with the correct scopes.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

