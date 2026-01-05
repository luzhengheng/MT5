# TASK #034 - Secrets Management Guide
## Secure Handling of Credentials and API Keys

**Status**: Security Critical
**Date**: 2026-01-05
**Protocol**: v4.2 (Agentic-Loop)

---

## Table of Contents

1. [Overview](#overview)
2. [Credentials Inventory](#credentials-inventory)
3. [DingTalk Webhook URL Acquisition](#dingtalk-webhook-url-acquisition)
4. [Secrets Configuration](#secrets-configuration)
5. [Secure Storage](#secure-storage)
6. [Secret Rotation](#secret-rotation)
7. [Access Control](#access-control)
8. [Incident Response](#incident-response)
9. [Compliance Checklist](#compliance-checklist)

---

## Overview

This guide provides secure procedures for managing all credentials and API keys used in the MT5-CRS production deployment. Secrets are critical to system security and must be protected with the highest standards.

### Secret Categories

| Category | Items | Sensitivity | Rotation |
|----------|-------|-------------|----------|
| **Credentials** | Dashboard password | CRITICAL | 90 days |
| **API Keys** | DingTalk webhook token | CRITICAL | 90 days |
| **Signing Keys** | DingTalk secret | CRITICAL | 90 days |
| **Database** | Postgres password | HIGH | 180 days |

---

## Credentials Inventory

### 1. Dashboard Access Credentials

**Purpose**: Protect Streamlit dashboard via Nginx Basic Auth

**Credential**:
```
Username: admin
Password: MT5Hub@2025!Secure
```

**Where Stored**:
- Nginx htpasswd: `/etc/nginx/.htpasswd` (hashed, root-readable only)
- Environment: NOT in .env (htpasswd used instead)

**Rotation**: Every 90 days

**Who Has Access**:
- DevOps/System administrators
- On-call engineers

### 2. DingTalk Webhook URL

**Purpose**: Send real-time notifications to DingTalk group

**Format**:
```
https://oapi.dingtalk.com/robot/send?access_token=XXXXXXXXXXXXX
```

**Where Stored**:
- Environment file: `/opt/mt5-crs/.env` (user-readable, should be restricted)
- Git: NOT committed (in .gitignore)
- Backups: Secure backup location only

**Rotation**: Every 90 days (coordinate with DingTalk admin)

**Who Has Access**:
- DevOps team (production)
- Platform engineers
- Risk management team (read-only for testing)

### 3. DingTalk Secret

**Purpose**: Sign messages for DingTalk webhook authentication (HMAC-SHA256)

**Value**:
```
SEC7d7cbd2505332b3ed3053f87dadfd2bbac9b0c2ba46d63d7c587351f3bb08de5
```

**Where Stored**:
- Environment file: `/opt/mt5-crs/.env`
- Code: Never hardcoded (loaded from env only)
- Git: NOT committed (in .gitignore)

**Format**: `SEC` prefix followed by 64-character hex string

**Rotation**: Every 90 days (when DingTalk webhook is rotated)

**Who Has Access**:
- DevOps team only
- Application runtime environment

---

## DingTalk Webhook URL Acquisition

### Step 1: Access DingTalk Group

1. Open DingTalk desktop application
2. Locate the target group for risk alerts (e.g., "MT5-CRS Risk Alerts")
3. Right-click on group name → Open group settings

### Step 2: Add Robot/Integration

1. In group settings, look for "Add Robot" or "Integration" option
2. Click to open robot management panel
3. Select "Create New Robot"

### Step 3: Configure Robot Details

1. **Robot Type**: Select "Custom Robot - Send Messages Any Time"
   - (Allows API calls to send messages without user action)

2. **Robot Name**: Enter `MT5-CRS Risk Monitor`

3. **Description**:
   ```
   Automated risk management and kill switch alerts for MT5-CRS trading system.
   Sends actionable notifications for risk violations and emergency situations.
   ```

4. **Icon**: Choose professional icon (optional, but recommended)

### Step 4: Enable Security

1. **Enable Signature Verification**: ✅ CRITICAL - This is required
   - Toggle: "Sign messages"
   - DingTalk will generate a secret

2. **Copy the Secret**
   - DingTalk displays: `SEC7d7cbd2505332b3ed3053f87dadfd2bbac9b0c2ba46d63d7c587351f3bb08de5`
   - **SAVE THIS VALUE** - This is your DINGTALK_SECRET

3. **Optional: IP Whitelist**
   - Add server IP address to whitelist if available
   - Format: `1.2.3.4` (production server IP)

### Step 5: Generate Webhook URL

1. Click "Generate Robot" or "Create Robot"
2. DingTalk displays the complete webhook URL:
   ```
   https://oapi.dingtalk.com/robot/send?access_token=1234567890abcdef...
   ```

3. **SAVE THIS URL** - This is your DINGTALK_WEBHOOK_URL
   - Copy the complete URL including `access_token` parameter
   - Keep secure (treat as sensitive as a password)

### Step 6: Test Connection

Before using in production, test the webhook:

```bash
# Test webhook connectivity
WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN_HERE"

curl -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "msgtype": "text",
    "text": {
      "content": "Test message from MT5-CRS system"
    }
  }'

# Expected response:
# {"errcode":0,"errmsg":"ok"}

# If you get error, verify:
# 1. URL is complete and correct
# 2. Token is not expired
# 3. Network connectivity to api.dingtalk.com
```

### Step 7: Document Access

Create a secure record:

```bash
# For internal documentation only (NOT in git or .env)
cat > /tmp/dingtalk_webhook_info.txt << 'EOF'
DingTalk Webhook Configuration
Date Created: 2026-01-05
Robot Name: MT5-CRS Risk Monitor

WEBHOOK_URL: https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
WEBHOOK_SECRET: SEC7d7cbd2505332b3ed3053f87dadfd2bbac9b0c2ba46d63d7c587351f3bb08de5

DingTalk Group: MT5-CRS Risk Alerts
Created By: [Your Name]
Last Rotated: 2026-01-05
Next Rotation: 2026-04-05 (90 days)

Notes:
- Secret is used to sign messages with HMAC-SHA256
- Webhook token embedded in URL
- Update .env with actual webhook URL before deployment
EOF

# Store in secure location (password manager or vault)
# Remove /tmp/dingtalk_webhook_info.txt after integration
```

---

## Secrets Configuration

### Step 1: Create .env File

```bash
cd /opt/mt5-crs

# Copy production template
cp .env.production .env

# Verify it exists
ls -la .env
```

### Step 2: Update Secrets

Open `.env` in secure editor:

```bash
# Use restricted nano (terminal only, no GUI)
nano /opt/mt5-crs/.env
```

Find and update these lines:

```bash
# ============================================================
# Dashboard & Notification Configuration (TASK #033)
# ============================================================

# Public URL for dashboard access (no credentials needed, proxied through Nginx)
DASHBOARD_PUBLIC_URL=http://www.crestive.net

# DingTalk webhook configuration (PRODUCTION - Real Secrets)
# WEBHOOK_URL: https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN_HERE
# Obtain from: DingTalk group settings → Add Robot → Custom Robot
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=PASTE_YOUR_TOKEN_HERE

# DINGTALK_SECRET: Used to sign messages (HMAC-SHA256)
# Obtain from: DingTalk group settings → Robot settings → Copy Secret
DINGTALK_SECRET=SEC7d7cbd2505332b3ed3053f87dadfd2bbac9b0c2ba46d63d7c587351f3bb08de5

# Streamlit dashboard configuration
STREAMLIT_HOST=127.0.0.1
STREAMLIT_PORT=8501
```

### Step 3: Verify Configuration

```bash
# Verify all secrets are set
echo "=== Configuration Verification ==="
grep "DINGTALK" /opt/mt5-crs/.env
grep "DASHBOARD" /opt/mt5-crs/.env

# Check for incomplete values
if grep "YOUR_TOKEN_HERE" /opt/mt5-crs/.env; then
    echo "⚠️  WARNING: Placeholder tokens still in .env"
    echo "Update with actual webhook URL before starting services"
fi
```

### Step 4: Secure File Permissions

```bash
# Set restrictive permissions (user read/write only)
chmod 600 /opt/mt5-crs/.env

# Verify permissions
ls -l /opt/mt5-crs/.env
# Expected: -rw------- 1 root root ...

# Test readability by application user
if [ -r /opt/mt5-crs/.env ]; then
    echo "✅ .env readable by application"
else
    echo "❌ ERROR: .env not readable"
fi
```

### Step 5: Verify Secret Loading

```bash
# Source the .env file and verify secrets load
cd /opt/mt5-crs
source .env

# Check that secrets are accessible
if [ -z "$DINGTALK_SECRET" ]; then
    echo "❌ ERROR: DINGTALK_SECRET not loaded"
    exit 1
fi

if [ -z "$DINGTALK_WEBHOOK_URL" ]; then
    echo "❌ ERROR: DINGTALK_WEBHOOK_URL not loaded"
    exit 1
fi

echo "✅ All secrets loaded successfully"
echo "DINGTALK_SECRET: ${DINGTALK_SECRET:0:30}..."
echo "WEBHOOK_URL: ${DINGTALK_WEBHOOK_URL:0:50}..."
```

---

## Secure Storage

### 1. File Permissions

```bash
# .env file: User read/write only
chmod 600 /opt/mt5-crs/.env
chmod 600 /opt/mt5-crs/.env.bak*

# Nginx htpasswd: Root read-only, group read
chmod 640 /etc/nginx/.htpasswd

# Application directory: User read/execute, group read/execute
chmod 755 /opt/mt5-crs
chmod 755 /opt/mt5-crs/src
```

### 2. Encrypted Backup

```bash
# Create encrypted backup of .env
gpg --symmetric --cipher-algo AES256 /opt/mt5-crs/.env
# Prompts for passphrase - use strong password

# Result: /opt/mt5-crs/.env.gpg
# Store in secure location (separate from production server)

# To restore from backup:
gpg --decrypt /opt/mt5-crs/.env.gpg > /opt/mt5-crs/.env
chmod 600 /opt/mt5-crs/.env
```

### 3. Git Ignore Configuration

```bash
# Verify .gitignore excludes secrets
cat /opt/mt5-crs/.gitignore | grep -E "\.env|\.htpasswd|\.gpg"

# Expected:
# .env
# .env.*
# .htpasswd
# *.gpg

# If not present, add them:
echo "
# Secrets and credentials
.env
.env.*
.htpasswd
*.gpg
" >> /opt/mt5-crs/.gitignore
```

### 4. Access Audit Log

Create a simple access audit:

```bash
# Create audit log file
touch /opt/mt5-crs/var/logs/secrets_access.log
chmod 600 /opt/mt5-crs/var/logs/secrets_access.log

# Log access events (add to deployment scripts):
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Secrets accessed for: $USER" >> /opt/mt5-crs/var/logs/secrets_access.log
```

---

## Secret Rotation

### Rotation Schedule

```
Dashboard Password: Every 90 days
DingTalk Webhook: Every 90 days
DingTalk Secret: Every 90 days (synchronized with webhook)
Database Password: Every 180 days
```

### Step 1: Plan Rotation

1. **Announce Schedule**: Notify team 2 weeks in advance
2. **Schedule Downtime**: Plan 15-minute maintenance window
3. **Prepare Backup**: Ensure current secrets are backed up
4. **Test Procedure**: Dry-run rotation in development first

### Step 2: Rotate Dashboard Password

```bash
# On production server with sudo access

# Step 1: Generate new password (strong format)
# Use pattern: RandomWord+RandomNumber!YYYY
# Example: SecurePass@2026!

# Step 2: Update htpasswd
NEW_PASSWORD="SecurePass@2026!"
sudo htpasswd -bc /etc/nginx/.htpasswd admin "$NEW_PASSWORD"

# Step 3: Test with new credentials
curl -u admin:"$NEW_PASSWORD" http://localhost/
# Expected: HTTP 200 OK

# Step 4: Reload Nginx
sudo systemctl reload nginx

# Step 5: Document (in secure location, NOT in git)
echo "Password rotated on $(date)" > /tmp/rotation_log.txt

# Step 6: Notify team of new password through secure channel
```

### Step 3: Rotate DingTalk Webhook

```bash
# Contact: DingTalk admin or your group administrator

# Step 1: Request new webhook URL
# - Access DingTalk group settings
# - Go to Robot → MT5-CRS Risk Monitor
# - Click "Generate New Token" or "Refresh Webhook"

# Step 2: Receive new webhook URL
# NEW_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=NEW_TOKEN"
# NEW_SECRET="SEC7d7cbd2505332b3ed3053f87dadfd2bbac9b0c2ba46d63d7c587351f3bb08de5"

# Step 3: Update .env on production
nano /opt/mt5-crs/.env
# Update:
# DINGTALK_WEBHOOK_URL=<new_webhook>
# DINGTALK_SECRET=<new_secret>

# Step 4: Test connectivity
cd /opt/mt5-crs
source .env
python3 -c "
from src.dashboard import send_risk_alert
result = send_risk_alert('ROTATION_TEST', 'DingTalk rotation test', 'INFO', 'dashboard')
print('✅ Webhook working' if result else '❌ Webhook failed')
"

# Step 5: Verify in DingTalk group
# - Check that test message arrived
# - Check that message is properly signed
# - Verify no error messages

# Step 6: Archive old webhook URL
# Store in secure backup with date
echo "OLD: https://oapi.dingtalk.com/robot/send?access_token=OLD_TOKEN [$(date)]" >> /tmp/retired_tokens.txt
rm /tmp/retired_tokens.txt  # Delete after archiving in secure location
```

### Step 4: Post-Rotation Verification

```bash
# 1. Run full test suite
cd /opt/mt5-crs
python3 scripts/uat_task_034.py

# 2. Check logs for errors
tail -50 /opt/mt5-crs/var/logs/streamlit.log | grep -i error

# 3. Verify dashboard access
curl -u admin:NEW_PASSWORD http://www.crestive.net/ | head -20

# 4. Send test DingTalk alert
python3 scripts/test_dingtalk_card.py

# 5. Monitor for 24 hours
# Check logs hourly for any authentication failures
watch -n 3600 'tail -10 /var/log/nginx/dashboard_access.log'
```

---

## Access Control

### Who Needs Access

| Role | Dashboard | Webhook URL | Secret | Database |
|------|-----------|------------|--------|----------|
| **DevOps** | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **On-Call** | ✅ Full | ❌ View | ❌ View | ❌ None |
| **Engineers** | ✅ Full | ❌ None | ❌ None | ✅ Full |
| **Traders** | ✅ View | ❌ None | ❌ None | ❌ None |
| **Audit** | ❌ None | ❌ Log | ❌ Log | ❌ Log |

### Access Procedures

```bash
# For viewing .env (DevOps only)
sudo cat /opt/mt5-crs/.env | grep DINGTALK

# For rotating passwords (2-person approval required)
# 1. Create change ticket with approval
# 2. Execute with sudo
# 3. Document rotation in audit log

# For reading logs (everyone)
tail /var/log/nginx/dashboard_access.log
tail /opt/mt5-crs/var/logs/streamlit.log
```

### Principle of Least Privilege

```bash
# Application user should only have permission to read .env
# Not modify it

# Create application user
sudo useradd -r -s /bin/bash mt5app || true

# Set permissions
sudo chown root:mt5app /opt/mt5-crs/.env
sudo chmod 640 /opt/mt5-crs/.env

# Verify
ls -l /opt/mt5-crs/.env
# Expected: -rw-r----- 1 root mt5app
```

---

## Incident Response

### Scenario 1: Webhook URL Leaked

**Severity**: CRITICAL

**Immediate Actions**:
1. Kill all running Streamlit processes: `pkill -9 -f streamlit`
2. Request new webhook URL from DingTalk immediately
3. Update .env with new URL
4. Restart services
5. Review access logs: `grep "DINGTALK" /var/log/nginx/dashboard_access.log`

**Within 1 Hour**:
6. Document what happened in incident report
7. Review who had access to .env
8. Audit git history for accidental commits

**Within 24 Hours**:
9. Complete root cause analysis
10. Implement preventive measures
11. Notify affected teams

### Scenario 2: .env File Committed to Git

**Severity**: CRITICAL

**Immediate Actions**:
1. Assume all secrets in that commit are compromised
2. Request new webhook URL, password, and secret
3. Rotate all credentials immediately
4. Push a new commit with updated credentials removed from history

**Git History Cleanup**:
```bash
# Remove file from git history (WARNING: destructive)
git filter-branch --tree-filter 'rm -f .env' HEAD

# Force push to remove history
git push --force-all

# Notify all developers to re-clone repository
```

### Scenario 3: Unauthorized .env Access

**Severity**: HIGH

**Investigation**:
```bash
# Check who accessed .env
sudo lastlog -f /opt/mt5-crs/.env

# Check file modification times
ls -la --time-style=full-iso /opt/mt5-crs/.env

# Check for copies
find /home -name ".env*" 2>/dev/null
find /tmp -name ".env*" 2>/dev/null

# Review system logs
sudo grep "/opt/mt5-crs/.env" /var/log/auth.log
```

**Response**:
1. Rotate all secrets immediately
2. Audit access logs for the time period
3. Disable user accounts if needed
4. File incident report with security team

### Scenario 4: DingTalk Notifications Failing

**Severity**: HIGH

**Diagnostic**:
```bash
# 1. Verify webhook URL is set
grep "DINGTALK_WEBHOOK_URL" /opt/mt5-crs/.env

# 2. Test connectivity
curl -I "$(grep DINGTALK_WEBHOOK_URL /opt/mt5-crs/.env | cut -d= -f2)"

# 3. Check application logs
tail -100 /opt/mt5-crs/var/logs/streamlit.log | grep -i dingtalk

# 4. Verify secret matches
grep "DINGTALK_SECRET" /opt/mt5-crs/.env
# Compare with DingTalk group settings

# 5. Test manually
cd /opt/mt5-crs
source .env
python3 scripts/test_dingtalk_card.py
```

**Resolution**:
- If webhook expired: Request new one from DingTalk
- If secret wrong: Update .env with correct secret
- If network issue: Check firewall rules to api.dingtalk.com
- If rate limited: Wait and retry (DingTalk has rate limits)

---

## Compliance Checklist

### Daily

- [ ] Review dashboard access logs for suspicious patterns
- [ ] Check Streamlit logs for authentication errors
- [ ] Verify DingTalk notifications are being sent

### Weekly

- [ ] Audit user access to .env file
- [ ] Verify secrets are not logged in plaintext
- [ ] Test dashboard authentication with correct/incorrect passwords
- [ ] Confirm backup of .env exists in secure location

### Monthly

- [ ] Review all password rotation dates
- [ ] Check for any hardcoded secrets in source code
- [ ] Audit git history for accidental commits
- [ ] Update access control list
- [ ] Run full penetration test on dashboard auth

### Quarterly

- [ ] Rotate dashboard password (90-day cycle)
- [ ] Rotate DingTalk webhook and secret (90-day cycle)
- [ ] Review and update this secrets management guide
- [ ] Conduct security training with team
- [ ] External security audit (if required)

### Checklist Template

```bash
# Save and run quarterly
cat > /tmp/compliance_check.sh << 'EOF'
#!/bin/bash

echo "=== SECRETS MANAGEMENT COMPLIANCE CHECK ==="
echo "Date: $(date)"
echo ""

# Check file permissions
echo "✓ File Permissions:"
ls -l /opt/mt5-crs/.env | awk '{print "  .env: " $1}'
ls -l /etc/nginx/.htpasswd 2>/dev/null | awk '{print "  .htpasswd: " $1}'

# Check for hardcoded secrets
echo ""
echo "✓ Code Review (checking for hardcoded secrets):"
grep -r "SEC7d7cbd" /opt/mt5-crs/src 2>/dev/null && echo "  ⚠️  WARNING: Secret found in source code" || echo "  ✅ No hardcoded secrets in source"

# Check git ignore
echo ""
echo "✓ Git Configuration:"
grep ".env" /opt/mt5-crs/.gitignore && echo "  ✅ .env in gitignore" || echo "  ❌ .env not in gitignore"

# Check backups exist
echo ""
echo "✓ Backup Status:"
ls -la /opt/mt5-crs/.env.bak* 2>/dev/null | wc -l | xargs echo "  Backup files found:"

echo ""
echo "=== END COMPLIANCE CHECK ==="
EOF

chmod +x /tmp/compliance_check.sh
bash /tmp/compliance_check.sh
```

---

## Additional Resources

- **OWASP Secrets Management**: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- **DingTalk Documentation**: https://open.dingtalk.com/
- **Nginx Authentication**: https://nginx.org/en/docs/http/ngx_http_auth_basic_module.html
- **Git Security**: https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work

---

**Document Version**: 1.0
**Last Updated**: 2026-01-05
**Classification**: Security Critical
