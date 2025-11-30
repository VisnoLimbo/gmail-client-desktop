#!/usr/bin/env python3
"""
Verify what scopes are actually in an OAuth access token by calling Google's tokeninfo API.
This helps diagnose if the token has the required IMAP scope.
"""

import sys
import os
import json
import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from email_client.auth.accounts import list_accounts, get_token_bundle
    
    print("=" * 60)
    print("Token Scope Verification (via Google API)")
    print("=" * 60)
    print()
    
    # Get all accounts
    accounts = list_accounts()
    
    if not accounts:
        print("No accounts found in the database.")
        sys.exit(0)
    
    for account in accounts:
        if account.auth_type != "oauth":
            print(f"Account: {account.email_address}")
            print(f"  Type: {account.auth_type} (not OAuth, skipping)")
            print()
            continue
        
        print(f"Account: {account.email_address} (ID: {account.id})")
        print()
        
        try:
            token_bundle = get_token_bundle(account.id)
            
            if not token_bundle or not token_bundle.access_token:
                print("  ✗ No access token found")
                print()
                continue
            
            access_token = token_bundle.access_token
            print(f"  Token length: {len(access_token)}")
            print()
            print("  Checking token scopes via Google's tokeninfo API...")
            
            # Call Google's tokeninfo endpoint
            try:
                response = requests.get(
                    "https://www.googleapis.com/oauth2/v1/tokeninfo",
                    params={"access_token": access_token},
                    timeout=10
                )
                
                if response.status_code != 200:
                    print(f"  ✗ Error from Google API: {response.status_code}")
                    print(f"  Response: {response.text[:200]}")
                    print()
                    continue
                
                token_info = response.json()
                
                # Check for errors
                if "error" in token_info:
                    error = token_info.get("error", "Unknown error")
                    error_description = token_info.get("error_description", "")
                    print(f"  ✗ Google API returned error: {error}")
                    if error_description:
                        print(f"  Description: {error_description}")
                    print()
                    continue
                
                # Extract scopes
                scope_str = token_info.get("scope", "")
                if scope_str:
                    scopes = scope_str.split()
                    print(f"  Token has {len(scopes)} scope(s):")
                    print()
                    
                    has_imap_scope = "https://mail.google.com/" in scopes
                    
                    for scope in sorted(scopes):
                        marker = "✓" if scope == "https://mail.google.com/" else " "
                        print(f"    {marker} {scope}")
                    
                    print()
                    
                    if has_imap_scope:
                        print("  ✓ IMAP scope (https://mail.google.com/) is PRESENT in token!")
                        print("  ✓ Token should work for IMAP authentication")
                    else:
                        print("  ✗ IMAP scope (https://mail.google.com/) is MISSING from token!")
                        print("  ✗ Token will NOT work for IMAP authentication")
                        print()
                        print("  → You need to remove and re-add this account to get a new token")
                        print("  → Make sure the scope is added to Google Cloud Console OAuth consent screen")
                        print("  → During re-authentication, check terminal logs for scope verification")
                else:
                    print("  ⚠ No scopes found in token info")
                
                # Also show other token info
                print()
                print("  Token info:")
                print(f"    Email: {token_info.get('email', 'N/A')}")
                print(f"    Expires in: {token_info.get('expires_in', 'N/A')} seconds")
                print(f"    Audience: {token_info.get('audience', 'N/A')}")
                print()
                
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Error calling Google API: {e}")
                print()
            except json.JSONDecodeError as e:
                print(f"  ✗ Error parsing Google API response: {e}")
                print()
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 60)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

