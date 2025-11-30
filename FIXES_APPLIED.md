# OAuth Authentication Fixes - Summary

## Problem
OAuth authentication was succeeding (token received), but accounts were not being logged in/synced properly.

## Root Causes Identified

1. **Empty Email Address**: `account_data['email']` was an empty string when OAuth started
2. **No User Info Fetch**: Email address was never fetched from Google after OAuth
3. **Token Expiration**: Incorrect handling of token expiration times
4. **Account Selection Race**: Account selection might happen before account is fully created
5. **Poor Error Handling**: Failures were not clearly communicated

## Fixes Applied

### 1. Added User Info Fetching from Google OAuth API
- **File**: `email_client/oauth2_handler.py`
- **Changes**:
  - Added `_fetch_google_user_info()` method to call Google's userinfo API
  - Fetches email, name, and picture after token exchange
  - Stores user info in token dictionary for account creation
  - Returns error if user info fetch fails (required for account creation)

### 2. Added Userinfo Scopes to Gmail OAuth
- **File**: `config.py`
- **Changes**:
  - Added `https://www.googleapis.com/auth/userinfo.email` scope
  - Added `https://www.googleapis.com/auth/userinfo.profile` scope
  - Required for fetching user email and name from Google

### 3. Fixed Account Creation to Use OAuth Email
- **File**: `ui/main_window.py`
- **Changes**:
  - Modified `_complete_account_setup_after_oauth()` to use email from token data
  - Email now comes from `token_data.get('user_email')` instead of empty `account_data['email']`
  - Added validation to ensure email is not empty before creating account
  - Uses display name from Google user info or falls back to account_data

### 4. Improved Token Expiration Handling
- **File**: `email_client/oauth2_handler.py`
- **Changes**:
  - Checks `credentials.expiry` attribute for expiration time
  - Calculates `expires_in` from expiry datetime
  - Falls back to default 3600 seconds if expiry not available

### 5. Fixed Account Selection and Sync Timing
- **File**: `ui/main_window.py`
- **Changes**:
  - Modified `load_accounts()` to accept optional `select_account_id` parameter
  - Prevents auto-selecting first account when we want to select newly created one
  - Added `_select_and_sync_account()` helper method
  - Uses QTimer to delay account selection until after UI updates
  - Ensures account is properly selected and synced after creation

### 6. Enhanced Error Handling
- **File**: `ui/main_window.py`, `email_client/oauth2_handler.py`
- **Changes**:
  - Clear error messages when user info fetch fails
  - Validation that account has valid ID before proceeding
  - Better error messages shown to user
  - Improved logging throughout the flow

## Testing Recommendations

1. **Test OAuth Flow**:
   - Click "Use Google Account" button
   - Complete authentication in browser
   - Verify account is created with correct email address
   - Verify account appears in sidebar
   - Verify account is automatically selected
   - Verify folders are synced

2. **Test Error Cases**:
   - Cancel authentication dialog - should allow cancellation
   - Deny permissions in browser - should show clear error
   - Network failure during userinfo fetch - should show error

3. **Verify Database**:
   - Check that account is saved with correct email
   - Verify token bundle is encrypted and stored
   - Check that account has correct provider and auth_type

## Notes

- The userinfo fetch is now **required** - if it fails, authentication fails
- Email address is **always** fetched from Google, never from user input
- Account selection is now deterministic (selects specific account, not just first)
- All error cases should now show clear messages to the user

