# Custom IMAP/SMTP Setup Guide

This guide explains how to set up and add email accounts using custom IMAP/SMTP servers in the Email Desktop Client. This is useful for:
- Private email servers
- Corporate email accounts
- Email providers not directly supported (Gmail, Outlook, Yahoo)
- Self-hosted email services

## Prerequisites

Before setting up a custom IMAP/SMTP account, ensure you have:
- Your email address
- Your email password or app-specific password
- IMAP server address and port
- SMTP server address and port
- Information about security settings (TLS/SSL requirements)

## Step-by-Step Setup

### 1. Gather Your Server Information

Contact your email provider or IT administrator to obtain:
- **IMAP Server**: The incoming mail server address (e.g., `imap.example.com`)
- **IMAP Port**: Usually `993` (with SSL/TLS) or `143` (with STARTTLS)
- **SMTP Server**: The outgoing mail server address (e.g., `smtp.example.com`)
- **SMTP Port**: Usually `465` (with SSL/TLS) or `587` (with STARTTLS)
- **Security**: Whether TLS/SSL is required

### 2. Common Server Settings

Here are common settings for popular providers:

#### Gmail (Custom Setup)
- **IMAP Server**: `imap.gmail.com`
- **IMAP Port**: `993`
- **SMTP Server**: `smtp.gmail.com`
- **SMTP Port**: `587`
- **Security**: TLS/SSL enabled
- **Note**: Requires an [App Password](https://myaccount.google.com/apppasswords), not your regular password

#### Outlook/Hotmail (Custom Setup)
- **IMAP Server**: `outlook.office365.com`
- **IMAP Port**: `993`
- **SMTP Server**: `smtp.office365.com`
- **SMTP Port**: `587`
- **Security**: TLS/SSL enabled

#### Yahoo Mail (Custom Setup)
- **IMAP Server**: `imap.mail.yahoo.com`
- **IMAP Port**: `993`
- **SMTP Server**: `smtp.mail.yahoo.com`
- **SMTP Port**: `587`
- **Security**: TLS/SSL enabled
- **Note**: Requires an [App Password](https://login.yahoo.com/account/security/app-passwords)

#### Zoho Mail
- **IMAP Server**: `imap.zoho.com`
- **IMAP Port**: `993`
- **SMTP Server**: `smtp.zoho.com`
- **SMTP Port**: `587`
- **Security**: TLS/SSL enabled

#### ProtonMail (Bridge Required)
- ProtonMail requires their Bridge application to work with IMAP/SMTP
- See [ProtonMail Bridge documentation](https://proton.me/mail/bridge) for setup

### 3. Adding the Account in the Application

1. **Open the Login Window**
   - Launch the Email Desktop Client
   - Click "Add Account" or open the login window

2. **Select Custom IMAP/SMTP**
   - In the "Select Email Provider" dropdown, choose "Custom IMAP/SMTP"

3. **Enter Account Information**
   - **Email Address**: Your full email address
   - **Password**: Your email password or app-specific password
   - **Display Name**: Your name (optional, defaults to email username)

4. **Configure Server Settings**
   - **IMAP Server**: Enter your IMAP server address
   - **IMAP Port**: Enter the IMAP port (usually `993` or `143`)
   - **SMTP Server**: Enter your SMTP server address
   - **SMTP Port**: Enter the SMTP port (usually `587` or `465`)
   - **Use TLS/SSL**: Check this box if your server requires encrypted connections (recommended)

5. **Add the Account**
   - Click "Add Account" to connect
   - The application will test the connection and sync your folders

## Troubleshooting

### Connection Failed Errors

**Problem**: "Connection failed" or "Authentication failed"

**Solutions**:
- Verify your email address and password are correct
- Check that server addresses are correct (no typos)
- Ensure port numbers match your provider's requirements
- Try enabling/disabling TLS/SSL
- Check if your provider requires an app-specific password instead of your regular password

### Port Connection Errors

**Problem**: "Connection refused" on specific ports

**Solutions**:
- Try alternative ports:
  - IMAP: `143` (STARTTLS) instead of `993` (SSL)
  - SMTP: `587` (STARTTLS) instead of `465` (SSL)
- Check if your firewall or network is blocking these ports
- Verify with your IT administrator that these ports are allowed

### SSL/TLS Certificate Errors

**Problem**: "SSL certificate verification failed"

**Solutions**:
- Verify you're using the correct server address
- Ensure TLS/SSL is enabled if your server requires it
- Contact your email provider if certificate issues persist

### Authentication Errors

**Problem**: "Invalid credentials" or "Authentication failed"

**Solutions**:
- Double-check your email address and password
- For Gmail/Yahoo: Use an app-specific password instead of your regular password
- For corporate email: Check if 2FA is enabled and you need an app password
- Verify your account isn't locked or suspended

### Common Port and Security Combinations

| Server Type | Port | Security | Common Use |
|------------|------|----------|------------|
| IMAP | 993 | SSL/TLS | Modern servers (recommended) |
| IMAP | 143 | STARTTLS | Older servers or corporate |
| SMTP | 587 | STARTTLS | Modern servers (recommended) |
| SMTP | 465 | SSL/TLS | Some legacy servers |
| SMTP | 25 | None | Usually blocked by ISPs |

## Security Best Practices

1. **Use App Passwords**
   - For Gmail, Yahoo, and other providers that support it, use app-specific passwords
   - These are more secure than using your main account password

2. **Enable TLS/SSL**
   - Always enable TLS/SSL for encrypted connections
   - This protects your credentials and email content during transmission

3. **Regular Password Updates**
   - Change your passwords regularly
   - Use strong, unique passwords for each account

4. **Firewall Configuration**
   - Ensure your firewall allows connections to IMAP/SMTP ports
   - Only allow connections to trusted servers

## Advanced Configuration

### Corporate/Enterprise Email

For corporate email accounts, you may need to:
- Use internal server addresses (e.g., `mail.company.com`)
- Configure special authentication methods (LDAP, OAuth)
- Use VPN if servers are only accessible on company network
- Contact your IT department for specific settings

### Self-Hosted Email Servers

If you're running your own email server:
- Ensure IMAP and SMTP services are running
- Configure firewall rules to allow connections
- Set up proper SSL/TLS certificates
- Verify authentication methods are enabled

### Testing Connection Settings

You can test your IMAP/SMTP settings using command-line tools:

**Test IMAP**:
```bash
# Using openssl (for SSL connection)
openssl s_client -connect imap.example.com:993

# Using telnet (for STARTTLS)
telnet imap.example.com 143
```

**Test SMTP**:
```bash
# Using openssl (for SSL connection)
openssl s_client -connect smtp.example.com:465

# Using telnet (for STARTTLS)
telnet smtp.example.com 587
```

## Getting Help

If you're still experiencing issues:
1. Check your email provider's documentation for IMAP/SMTP settings
2. Contact your IT administrator (for corporate email)
3. Review the application logs in `~/.email_client/logs/app.log`
4. Verify network connectivity and firewall settings

## Additional Resources

- [Gmail IMAP Settings](https://support.google.com/mail/answer/7126229)
- [Outlook IMAP Settings](https://support.microsoft.com/en-us/office/pop-imap-and-smtp-settings-8361e398-8af4-4e97-b147-6c6c4ac95353)
- [Yahoo IMAP Settings](https://help.yahoo.com/kb/SLN4075.html)
- [IMAP Protocol RFC](https://tools.ietf.org/html/rfc3501)
- [SMTP Protocol RFC](https://tools.ietf.org/html/rfc5321)

## Quick Reference Table

| Provider | IMAP Server | IMAP Port | SMTP Server | SMTP Port | Notes |
|----------|-------------|-----------|-------------|-----------|-------|
| Gmail | imap.gmail.com | 993 | smtp.gmail.com | 587 | App password required |
| Outlook | outlook.office365.com | 993 | smtp.office365.com | 587 | - |
| Yahoo | imap.mail.yahoo.com | 993 | smtp.mail.yahoo.com | 587 | App password required |
| Zoho | imap.zoho.com | 993 | smtp.zoho.com | 587 | - |
| FastMail | imap.fastmail.com | 993 | smtp.fastmail.com | 587 | - |
| iCloud | imap.mail.me.com | 993 | smtp.mail.me.com | 587 | App password required |

---

**Note**: Server settings may vary. Always verify with your email provider's current documentation.

