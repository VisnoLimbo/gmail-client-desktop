#!/usr/bin/env python3
"""
Helper script to verify OAuth scopes are properly configured.
This script checks:
1. That the required scopes are in config.py
2. That the IMAP scope is being requested
3. Shows what scopes should be in Google Cloud Console
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import config
    
    print("=" * 60)
    print("OAuth Scope Verification")
    print("=" * 60)
    print()
    
    print("1. Checking Gmail scopes in config.py:")
    print(f"   Total scopes: {len(config.GMAIL_SCOPES)}")
    print()
    
    required_imap_scope = "https://mail.google.com/"
    has_imap_scope = required_imap_scope in config.GMAIL_SCOPES
    
    print(f"   ✓ Required IMAP scope '{required_imap_scope}' is {'PRESENT' if has_imap_scope else 'MISSING'}")
    print()
    
    print("2. All Gmail scopes configured:")
    for i, scope in enumerate(config.GMAIL_SCOPES, 1):
        marker = "✓" if scope == required_imap_scope else " "
        print(f"   {marker} {i}. {scope}")
    print()
    
    print("3. Google Cloud Console Configuration:")
    print("   Please ensure ALL of these scopes are added to your OAuth consent screen:")
    print()
    for scope in config.GMAIL_SCOPES:
        print(f"   - {scope}")
    print()
    
    if has_imap_scope:
        print("✓ Configuration looks correct!")
        print()
        print("Next steps:")
        print("1. Verify the scope 'https://mail.google.com/' is in Google Cloud Console")
        print("2. Remove the existing account from the app")
        print("3. Re-add the account to get a new token with the scope")
        print("4. Check the terminal output during authentication for scope verification")
    else:
        print("✗ ERROR: Required IMAP scope is missing from config.py!")
        print(f"   Please add '{required_imap_scope}' to GMAIL_SCOPES in config.py")
        sys.exit(1)
    
    print()
    print("=" * 60)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

