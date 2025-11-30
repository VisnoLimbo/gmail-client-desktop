#!/usr/bin/env python3
"""
Diagnostic script to check OAuth configuration and token details.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import config
    from email_client.auth.accounts import list_accounts, get_token_bundle
    import requests
    
    print("=" * 60)
    print("OAuth Configuration Diagnostic")
    print("=" * 60)
    print()
    
    # Check config
    print("1. OAuth Configuration:")
    print(f"   GMAIL_CLIENT_ID: {config.GMAIL_CLIENT_ID[:20] + '...' if len(config.GMAIL_CLIENT_ID) > 20 else config.GMAIL_CLIENT_ID}")
    print(f"   GMAIL_CLIENT_ID length: {len(config.GMAIL_CLIENT_ID)}")
    print(f"   GMAIL_CLIENT_SECRET: {'***' + config.GMAIL_CLIENT_SECRET[-4:] if config.GMAIL_CLIENT_SECRET else 'NOT SET'}")
    print()
    
    # Get accounts
    accounts = list_accounts()
    oauth_accounts = [a for a in accounts if a.auth_type == "oauth"]
    
    if not oauth_accounts:
        print("No OAuth accounts found.")
        sys.exit(0)
    
    for account in oauth_accounts:
        print(f"2. Account: {account.email_address}")
        print()
        
        try:
            token_bundle = get_token_bundle(account.id)
            
            if not token_bundle or not token_bundle.access_token:
                print("   ✗ No access token found")
                continue
            
            # Get token info from Google
            response = requests.get(
                "https://www.googleapis.com/oauth2/v1/tokeninfo",
                params={"access_token": token_bundle.access_token},
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"   ✗ Error from Google API: {response.status_code}")
                continue
            
            token_info = response.json()
            
            if "error" in token_info:
                print(f"   ✗ Token error: {token_info.get('error')}")
                continue
            
            # Compare client IDs
            token_audience = token_info.get('audience', '')
            configured_client_id = config.GMAIL_CLIENT_ID
            
            print(f"   Token Audience (Client ID): {token_audience}")
            print(f"   Configured Client ID:       {configured_client_id}")
            print()
            
            if token_audience != configured_client_id:
                print("   ⚠ WARNING: Client ID mismatch!")
                print("   The token was issued for a different OAuth client than configured.")
                print("   This could cause IMAP authentication to fail.")
                print()
                print("   Solution:")
                print("   1. Make sure GMAIL_CLIENT_ID in .env matches the OAuth client used to create the token")
                print("   2. OR remove and re-add the account to get a token for the correct client")
            else:
                print("   ✓ Client IDs match")
            
            # Check scopes
            scopes = token_info.get('scope', '').split() if token_info.get('scope') else []
            has_imap = "https://mail.google.com/" in scopes
            
            print()
            print(f"   Token has {len(scopes)} scope(s)")
            print(f"   IMAP scope present: {'✓ YES' if has_imap else '✗ NO'}")
            print()
            
            if has_imap and token_audience == configured_client_id:
                print("   ✓ Token looks correct - it has the IMAP scope and matches the configured client")
                print()
                print("   If IMAP still fails, possible causes:")
                print("   1. Token might need to be refreshed")
                print("   2. Google IMAP server caching issue")
                print("   3. OAuth client not enabled for IMAP access in Google Cloud Console")
                print("   4. Need to wait a few minutes for changes to propagate")
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=" * 60)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

