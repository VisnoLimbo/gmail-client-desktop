# IMAP Authentication Troubleshooting

## Current Status

✅ **Token Verification**: The OAuth token HAS the required `https://mail.google.com/` scope  
✅ **Client ID Match**: Token was issued for the correct OAuth client ID  
✅ **Configuration**: All OAuth scopes are properly configured in `config.py`  
✅ **Google Cloud Console**: Scope is added to OAuth consent screen  

❌ **IMAP Authentication**: Still failing with scope error

## Error Message

```
IMAP: Received SASL challenge: b'{"status":"400","schemes":"Bearer","scope":"https://mail.google.com/"}'
IMAP authentication error: OAuth token is missing required scope for IMAP access.
Required scope: https://mail.google.com/
```

## Diagnosis

Even though the token has the scope (verified via Google's tokeninfo API), Google's IMAP server is rejecting it. This suggests:

1. **OAuth Client Configuration**: The OAuth client might not be properly enabled for IMAP/SMTP access
2. **Token Refresh Needed**: The token might need to be refreshed
3. **Google Server Caching**: Google's IMAP servers might be caching an old token state
4. **Authorization Timing**: Changes to OAuth consent screen might not have propagated yet

## Solutions to Try

### Solution 1: Verify OAuth Client Settings in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **APIs & Services** → **Credentials**
4. Click on your OAuth 2.0 Client ID
5. Check:
   - **Application type**: Should be "Desktop app" or "Web application"
   - **Authorized redirect URIs**: Should include `http://localhost:8080/callback`
   - **APIs Enabled**: Ensure Gmail API is enabled

6. Go to **APIs & Services** → **Library**
7. Search for "Gmail API" and ensure it's **ENABLED**

### Solution 2: Refresh the Token

The token might be valid but Google IMAP needs a fresh authentication. Try:

1. Remove the account from the app
2. Wait 5-10 minutes for Google's servers to clear any cached state
3. Re-add the account and complete OAuth flow
4. Watch terminal logs to verify scope is granted

### Solution 3: Check OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Verify these scopes are listed:
   - `https://mail.google.com/` (in Restricted scopes → Gmail scopes)
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
   - `openid`
3. If in "Testing" mode, add your email as a test user
4. Save and wait 5-10 minutes for changes to propagate

### Solution 4: Re-authorize the Application

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Go to **Security** → **Third-party apps with account access**
3. Find your app and click **Remove access**
4. Remove the account from the desktop app
5. Re-add the account to trigger a fresh OAuth flow

### Solution 5: Verify Scope is Actually Granted

During re-authentication, check terminal output for:

```
OAuth: Token granted with X scope(s): [...]
OAuth: IMAP scope (https://mail.google.com/) granted: True
```

If it shows `False`, the scope wasn't granted and you need to check Google Cloud Console settings.

## Diagnostic Tools

Run these scripts to verify configuration:

```bash
# Verify OAuth configuration
source venv/bin/activate
python verify_oauth_scopes.py

# Check token scopes via Google API
python verify_token_scopes.py

# Full OAuth diagnostic
python diagnose_oauth.py
```

## Next Steps

1. Try Solution 1 first (verify OAuth client and Gmail API are enabled)
2. If that doesn't work, try Solution 2 (refresh token)
3. Check terminal logs during re-authentication to see if scope is granted
4. If scope is granted but IMAP still fails, it's likely a Google server-side caching issue - wait 10-15 minutes and try again

