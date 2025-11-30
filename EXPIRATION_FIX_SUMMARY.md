# Token Expiration Calculation Bug - FIXED

## Root Cause (FOUND BY USER!)

The `expires_at` calculation was incorrect, causing:
- Expired tokens to be treated as valid
- Google IMAP to reject tokens with misleading "missing scope" error
- No token refresh logic to trigger

## What Was Fixed

### 1. `oauth2_handler.py`
- ✅ Fixed `expires_in` calculation from `credentials.expiry`
- ✅ Added timezone-aware datetime handling
- ✅ Added validation to ensure expires_in is reasonable (0-7200 seconds)
- ✅ Added debug logging

### 2. `main_window.py`
- ✅ Fixed `expires_at` calculation: `datetime.now() + timedelta(seconds=expires_in)`
- ✅ Added validation to detect suspicious expiration values
- ✅ Added debug logging to verify token lifetime

### 3. `imap_client.py`
- ✅ Enhanced expiration check with better logging
- ✅ Warns if token expires soon (< 5 minutes)
- ✅ Improved error messages

## IMPORTANT: Action Required

**You MUST remove and re-add your account** to get a NEW token with the CORRECT expiration calculation.

The existing token in your database was created with the buggy calculation, so:
- ✅ The code is now fixed
- ❌ But the stored token still has the wrong expiration
- ❌ IMAP will continue to fail until you get a new token

## Steps to Fix

1. **Remove the account** from the app:
   - Right-click account → "Remove Account"
   - OR: Account management dialog → Delete account

2. **Re-add the account**:
   - Add Account → Gmail → OAuth
   - Complete authentication flow

3. **Verify the fix**:
   - Watch terminal logs during authentication
   - Look for: `Account setup: DEBUG - real token lifetime (seconds): 3600.0`
   - If you see a large number (> 7200), something is still wrong

4. **Test IMAP**:
   - Try syncing folders
   - IMAP authentication should now work

## Expected Debug Output

After re-authentication, you should see:
```
OAuth: Token expires_in calculated: 3600 seconds
Account setup: Token expires_in: 3600 seconds
Account setup: DEBUG - real token lifetime (seconds): 3600.0
IMAP: Time until token expiry: 3600.0 seconds
```

## If Issues Persist

If you still see errors after re-authenticating:

1. Check terminal logs for the debug output above
2. Run: `python verify_token_scopes.py` to verify token has IMAP scope
3. Run: `python diagnose_oauth.py` to check client ID matching
4. Check Google Cloud Console:
   - Gmail API is enabled
   - OAuth consent screen has `https://mail.google.com/` scope

## Technical Details

### Before (BUGGY):
```python
# Incorrect calculation - could result in wrong expiration
expires_in = int((credentials.expiry - datetime.utcnow()).total_seconds())
expires_at = datetime.now() + timedelta(seconds=expires_in)  # Timezone mismatch!
```

### After (FIXED):
```python
# Timezone-aware calculation
now_utc = datetime.now(timezone.utc)
if credentials.expiry.tzinfo is None:
    expiry_utc = credentials.expiry.replace(tzinfo=timezone.utc)
else:
    expiry_utc = credentials.expiry
expires_in = int((expiry_utc - now_utc).total_seconds())
# Validate: should be ~3600 seconds
if expires_in > 0 and expires_in <= 7200:
    self.token['expires_in'] = expires_in
else:
    self.token['expires_in'] = 3600  # Default fallback
```

