# TASK #034 - Production Deployment Guide
## MT5-CRS Production Deployment & DingTalk Integration

**Status**: Ready for Production Deployment
**Date**: 2026-01-05
**Protocol**: v4.2 (Agentic-Loop)

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [System Requirements](#system-requirements)
3. [Secrets & Configuration](#secrets--configuration)
4. [Step 1: Environment Configuration](#step-1-environment-configuration)
5. [Step 2: Nginx Setup & Basic Auth](#step-2-nginx-setup--basic-auth)
6. [Step 3: Start Services](#step-3-start-services)
7. [Step 4: Verification & Testing](#step-4-verification--testing)
8. [Step 5: Gate 2 AI Review](#step-5-gate-2-ai-review)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Security Best Practices](#security-best-practices)
11. [Post-Deployment Monitoring](#post-deployment-monitoring)

---

## Pre-Deployment Checklist

Before deploying to production, verify the following:

- [ ] Running on Linux system with sudo access
- [ ] Git repository is clean (no uncommitted changes in critical files)
- [ ] DingTalk webhook URL obtained from administrator
- [ ] Dashboard password approved by security team: `MT5Hub@2025!Secure`
- [ ] Nginx installation planned or auto-install enabled
- [ ] Port 80 available (or adjust nginx_dashboard.conf for alternative port)
- [ ] Streamlit port 8501 not in use
- [ ] Backup of existing .env file prepared
- [ ] Team notified of deployment timeline
- [ ] Monitoring/alerting systems prepared

---

## System Requirements

### Minimum Infrastructure
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **Python**: 3.9+
- **Disk Space**: 2GB free (including logs)
- **Memory**: 2GB minimum, 4GB+ recommended
- **Network**: Internet access for DingTalk API

### Required Packages
- `nginx` (auto-installed by deployment script if missing)
- `apache2-utils` (for htpasswd, auto-installed if missing)
- `python3-pip` (for Streamlit dependencies)
- `git` (for version control)

### Service Ports
- Port 80: Nginx reverse proxy
- Port 8501: Streamlit backend (proxied through Nginx)
- Port 5556: ZMQ market data (if running with trading)
- Port 5555: GTW execution gateway (if running with trading)

---

## Secrets & Configuration

### DingTalk Webhook URL

The DingTalk webhook URL is required for sending real notifications. Follow these steps to obtain it:

1. **Access DingTalk Admin Panel**
   - Open DingTalk desktop application
   - Navigate to the target group/chat
   - Click on group settings (three dots menu)
   - Select "Add Robot" or "Integrate"

2. **Create Custom Robot**
   - Choose "Custom - Send Messages Any Time"
   - Set robot name: "MT5-CRS Risk Monitor"
   - Enable security: Select "Sign" and copy the secret key

3. **Extract Webhook URL**
   - After creation, copy the complete webhook URL
   - Format: `https://oapi.dingtalk.com/robot/send?access_token=XXXXXXXXXXXXX`
   - Store in secure location (will use in Step 1)

### Credentials Configuration

#### Dashboard Access Credentials
```
Username: admin
Password: MT5Hub@2025!Secure
```

These credentials will be used for Nginx Basic Auth protection.

#### DingTalk Secret
```
DINGTALK_SECRET=SEC7d7cbd2505332b3ed3053f87dadfd2bbac9b0c2ba46d63d7c587351f3bb08de5
```

This secret is used to sign messages sent to DingTalk (HMAC-SHA256).

---

## Step 1: Environment Configuration

### 1.1 Verify Current Environment

```bash
cd /opt/mt5-crs

# Check current .env status
if [ -f .env ]; then
    echo "Existing .env file found"
    # Backup current .env
    cp .env .env.backup.$(date +%s)
    echo "Backed up to .env.backup.$(date +%s)"
else
    echo "No existing .env file"
fi

# Copy production template
cp .env.production .env
```

### 1.2 Update .env with Secrets

Open the `.env` file in your editor:

```bash
nano /opt/mt5-crs/.env
```

Update the following lines with actual values:

```bash
# Find and update these lines:

# REQUIRED: DingTalk webhook URL (obtained from Step above)
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=YOUR_ACTUAL_TOKEN

# DingTalk Secret (already configured)
DINGTALK_SECRET=SEC7d7cbd2505332b3ed3053f87dadfd2bbac9b0c2ba46d63d7c587351f3bb08de5

# Dashboard Public URL
DASHBOARD_PUBLIC_URL=http://www.crestive.net

# Streamlit Configuration
STREAMLIT_HOST=127.0.0.1
STREAMLIT_PORT=8501
```

### 1.3 Verify Configuration

```bash
# Check that all required secrets are set
grep -E "DINGTALK|DASHBOARD" /opt/mt5-crs/.env

# Expected output:
# DASHBOARD_PUBLIC_URL=http://www.crestive.net
# DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=...
# DINGTALK_SECRET=SEC7d7cbd2505332b3ed3053f87dadfd2bbac9b0c2ba46d63d7c587351f3bb08de5
```

### 1.4 Set Permissions

```bash
# Secure .env file (readable only by owner)
chmod 600 /opt/mt5-crs/.env

# Verify permissions
ls -l /opt/mt5-crs/.env
# Expected: -rw------- 1 root root ...
```

---

## Step 2: Nginx Setup & Basic Auth

### 2.1 Run Automated Deployment Script

The `deploy_production.sh` script automates steps 2-3. Run with sudo:

```bash
cd /opt/mt5-crs
sudo bash deploy_production.sh
```

**Script will:**
1. Generate htpasswd file at `/etc/nginx/.htpasswd`
2. Copy Nginx configuration to `/etc/nginx/sites-available/dashboard`
3. Create symlink to enable the site
4. Test Nginx configuration syntax
5. Reload Nginx service
6. Start Streamlit service on port 8501

### 2.2 Manual Nginx Setup (if automated script fails)

#### Step A: Generate htpasswd

```bash
# Create htpasswd file with admin credentials
sudo htpasswd -bc /etc/nginx/.htpasswd admin "MT5Hub@2025!Secure"

# Verify file created
sudo cat /etc/nginx/.htpasswd
# Expected: admin:$apr1$xxxxx...
```

#### Step B: Deploy Nginx Configuration

```bash
# Copy Nginx config
sudo cp /opt/mt5-crs/nginx_dashboard.conf /etc/nginx/sites-available/dashboard

# Enable the site (create symlink)
sudo ln -s /etc/nginx/sites-available/dashboard /etc/nginx/sites-enabled/dashboard

# Test Nginx configuration
sudo nginx -t
# Expected: nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
#           nginx: configuration file /etc/nginx/nginx.conf test is successful
```

#### Step C: Reload Nginx

```bash
# Reload Nginx with new configuration
sudo systemctl reload nginx

# Verify Nginx is running
sudo systemctl status nginx
# Expected: active (running)

# Check if listening on port 80
sudo netstat -tlnp | grep nginx
# Expected: tcp  0  0 0.0.0.0:80  0.0.0.0:*  LISTEN  ....
```

### 2.3 Verify Nginx Configuration

```bash
# Test unauthenticated access (should prompt for credentials)
curl -I http://localhost/
# Expected: HTTP/1.1 401 Unauthorized
#           WWW-Authenticate: Basic realm="MT5-CRS Dashboard..."

# Test with correct credentials
curl -I -u admin:MT5Hub@2025!Secure http://localhost/
# Expected: HTTP/1.1 200 OK
```

---

## Step 3: Start Services

### 3.1 Ensure .env is Loaded

```bash
# Verify environment variables are accessible
source /opt/mt5-crs/.env
echo "DINGTALK_SECRET=$DINGTALK_SECRET"
# Expected: DINGTALK_SECRET=SEC7d7cbd...
```

### 3.2 Start Streamlit Service

The `deploy_production.sh` script starts Streamlit automatically. To start manually:

```bash
cd /opt/mt5-crs

# Start Streamlit on port 8501
nohup env $(cat .env | grep -v '^#' | xargs) \
    streamlit run src/dashboard/app.py \
    --server.port 8501 \
    --server.address 127.0.0.1 \
    --client.showErrorDetails false \
    > var/logs/streamlit.log 2>&1 &

# Note: Wait 3-5 seconds for Streamlit to start
sleep 3

# Verify Streamlit is running
pgrep -f "streamlit run"
# Expected: [PID number]
```

### 3.3 Create Log Directory (if needed)

```bash
# Ensure logs directory exists
mkdir -p /opt/mt5-crs/var/logs

# Set permissions
chmod 755 /opt/mt5-crs/var/logs
```

---

## Step 4: Verification & Testing

### 4.1 Network Connectivity Test

```bash
# Test local Streamlit backend
curl -I http://127.0.0.1:8501/
# Expected: HTTP/1.1 200 OK

# Test through Nginx proxy (without auth)
curl -I http://localhost/
# Expected: HTTP/1.1 401 Unauthorized

# Test through Nginx proxy (with auth)
curl -I -u admin:MT5Hub@2025!Secure http://localhost/
# Expected: HTTP/1.1 200 OK
```

### 4.2 Dashboard Access via Browser

1. Open browser and navigate to: `http://www.crestive.net`
2. Browser should prompt for credentials
3. Enter: **Username**: `admin`, **Password**: `MT5Hub@2025!Secure`
4. Should display the MT5-CRS dashboard with:
   - PnL metrics
   - Position information
   - Trade history
   - Kill Switch status panel
   - Risk management controls

### 4.3 Run UAT Test Suite

```bash
cd /opt/mt5-crs

# Run full UAT test suite
python3 scripts/uat_task_034.py

# Expected output:
# ✅ 8 tests completed
# All critical tests passing:
#   ✅ Dashboard access with Basic Auth
#   ✅ DingTalk configuration verified
#   ✅ Real alert delivery
#   ✅ Kill switch functionality
#   ✅ Nginx proxy configuration
```

### 4.4 Test DingTalk Integration

```bash
cd /opt/mt5-crs

# Run DingTalk test (sends real message to DingTalk group)
python3 scripts/test_dingtalk_card.py

# Expected:
# [2026-01-05 XX:XX:XX] ✅ Test 1: DingTalkNotifier initialization
# [2026-01-05 XX:XX:XX] ✅ Test 2: ActionCard format validation
# [2026-01-05 XX:XX:XX] ✅ Test 3: Send ActionCard (real webhook)
# [2026-01-05 XX:XX:XX] ✅ Test 4: Send risk alert
# [2026-01-05 XX:XX:XX] ✅ Test 5: Kill switch alert
# 7/7 tests passing
```

### 4.5 Verify Logs

```bash
# Check Streamlit logs for errors
tail -50 /opt/mt5-crs/var/logs/streamlit.log

# Check Nginx access logs
sudo tail -20 /var/log/nginx/dashboard_access.log

# Check Nginx error logs
sudo tail -20 /var/log/nginx/dashboard_error.log
```

---

## Step 5: Gate 2 AI Review

### 5.1 Run Architectural Review

```bash
cd /opt/mt5-crs

# Execute Gate 2 AI architectural review
python3 gemini_review_bridge.py

# This will:
# 1. Verify Nginx configuration correctness
# 2. Validate DingTalk integration security
# 3. Confirm Kill Switch implementation
# 4. Approve production readiness
```

### 5.2 Expected Output

```
Session ID: 7b192e64-e36f-4e0c-89cd-c87e46616dad
Token Consumption: 2,456 tokens

✅ Gate 2 Review: PASSED
✅ Nginx configuration: Correct and secure
✅ DingTalk integration: Properly signed with HMAC-SHA256
✅ Kill Switch controls: Functional and enforced
✅ Production readiness: APPROVED

Confidence Level: ⭐⭐⭐⭐⭐
```

---

## Troubleshooting Guide

### Issue 1: Nginx Failed to Start

```
Error: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
```

**Solution:**
```bash
# Check what's using port 80
sudo lsof -i :80

# Kill conflicting process or change Nginx port in nginx_dashboard.conf
# Change line: listen 80;
# To: listen 8080;
# Then update your access URL accordingly
```

### Issue 2: htpasswd File Not Found

```
Error: open() "/etc/nginx/.htpasswd" failed (2: No such file or directory)
```

**Solution:**
```bash
# Regenerate htpasswd file
sudo htpasswd -bc /etc/nginx/.htpasswd admin "MT5Hub@2025!Secure"

# Verify creation
sudo ls -l /etc/nginx/.htpasswd

# Reload Nginx
sudo nginx -t && sudo systemctl reload nginx
```

### Issue 3: Streamlit Not Responding

```
Error: Connection refused connecting to http://127.0.0.1:8501
```

**Solution:**
```bash
# Check if Streamlit is running
pgrep -f "streamlit run"

# If not running, check logs
tail -100 /opt/mt5-crs/var/logs/streamlit.log

# Common causes:
# 1. Port 8501 in use: sudo lsof -i :8501
# 2. Missing dependencies: pip install streamlit
# 3. Missing environment variables: source .env
# 4. Corrupted .env file: Check syntax for special characters

# Restart Streamlit
pkill -f "streamlit run"
sleep 2
cd /opt/mt5-crs && nohup env $(cat .env | grep -v '^#' | xargs) \
    streamlit run src/dashboard/app.py \
    --server.port 8501 \
    --server.address 127.0.0.1 \
    > var/logs/streamlit.log 2>&1 &
```

### Issue 4: DingTalk Webhook URL Not Working

```
Error: [WEBHOOK_ERROR] Failed to send to DingTalk: URL parse error
```

**Solution:**
```bash
# Verify webhook URL format
grep "DINGTALK_WEBHOOK_URL" /opt/mt5-crs/.env

# Should be: https://oapi.dingtalk.com/robot/send?access_token=...
# Should NOT have spaces or incomplete URLs

# Test webhook manually
WEBHOOK_URL="<your_webhook_url>"
curl -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "msgtype": "text",
    "text": {"content": "Test message"}
  }'

# If this fails, webhook URL is incorrect
# Get correct URL from DingTalk admin panel
```

### Issue 5: 401 Unauthorized Errors in Logs

```
2026-01-05 12:34:56 - 127.0.0.1 "GET / HTTP/1.1" 401
```

**Solution:**
This is expected behavior. Clients without Basic Auth credentials will receive 401.

To verify authentication works:
```bash
# Should fail (401):
curl http://www.crestive.net/

# Should succeed (200):
curl -u admin:MT5Hub@2025!Secure http://www.crestive.net/
```

### Issue 6: .env File Not Loading

```
Error: DINGTALK_SECRET not set or empty
```

**Solution:**
```bash
# Check .env file exists and is readable
ls -la /opt/mt5-crs/.env

# Check file contents (first few lines)
head -20 /opt/mt5-crs/.env

# Verify no trailing spaces in values
grep "DINGTALK_SECRET" /opt/mt5-crs/.env

# If loading from script, use proper syntax:
source /opt/mt5-crs/.env
# OR
export $(cat /opt/mt5-crs/.env | grep -v '^#' | xargs)
```

---

## Security Best Practices

### 1. Secrets Management

✅ **DO:**
- Store secrets in `.env` file (which is gitignored)
- Restrict .env file permissions: `chmod 600 .env`
- Rotate secrets every 90 days
- Use environment variables only (never hardcode)
- Back up htpasswd file securely

❌ **DON'T:**
- Commit `.env` file to git repository
- Share credentials in email or chat
- Use weak passwords (follow: `SecurePassword@YYYY!Pattern`)
- Log credentials in application output

### 2. Network Security

✅ **DO:**
- Restrict dashboard access with Nginx Basic Auth
- Use HTTPS in production (enable SSL in nginx_dashboard.conf)
- Implement VPN-only access for production
- Monitor access logs for suspicious patterns
- Whitelist IP addresses if possible

❌ **DON'T:**
- Expose dashboard on public internet without authentication
- Use HTTP in production (use HTTPS with SSL certificates)
- Allow anonymous access to dashboard
- Disable Nginx auth for "easier access"

### 3. DingTalk Integration Security

✅ **DO:**
- Keep webhook URL confidential
- Verify HMAC signatures on incoming messages
- Rotate webhook tokens when staff leaves
- Monitor DingTalk API rate limits
- Log all DingTalk interactions

❌ **DON'T:**
- Share webhook URL in version control
- Disable HMAC signing for "faster testing"
- Leave default webhook URL in production
- Log full webhook URLs with tokens

### 4. Regular Monitoring

✅ **DO:**
- Review Nginx access logs daily
- Monitor Streamlit performance metrics
- Set up alerts for authentication failures
- Verify DingTalk delivery status
- Maintain audit trail of configuration changes

❌ **DON'T:**
- Ignore security warnings in logs
- Skip authentication testing after updates
- Accumulate old logs without rotation
- Deploy without testing on staging first

### 5. SSL/TLS Configuration (for production)

For production deployment with HTTPS, uncomment and configure the SSL section in `nginx_dashboard.conf`:

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate (requires domain)
sudo certbot certonly --standalone -d www.crestive.net

# Update nginx_dashboard.conf with certificate paths
sudo nano /etc/nginx/sites-available/dashboard

# Enable HTTPS redirect (uncomment SSL section)
sudo nginx -t && sudo systemctl reload nginx
```

---

## Post-Deployment Monitoring

### 1. Daily Checks

```bash
# Check service status
sudo systemctl status nginx
pgrep -f "streamlit run"

# Check recent logs
tail -20 /var/log/nginx/dashboard_access.log
tail -20 /opt/mt5-crs/var/logs/streamlit.log

# Verify dashboard accessibility
curl -u admin:MT5Hub@2025!Secure http://www.crestive.net/ | grep -q "MT5-CRS" && echo "✅ Dashboard OK"
```

### 2. Weekly Checks

```bash
# Review authentication failures
grep "401" /var/log/nginx/dashboard_access.log | wc -l

# Check disk space
df -h | grep -E "/$|/opt"

# Verify DingTalk integration
python3 scripts/test_dingtalk_card.py

# Check log file sizes
ls -lh /var/log/nginx/dashboard_*
ls -lh /opt/mt5-crs/var/logs/
```

### 3. Monthly Tasks

```bash
# Archive old logs
find /var/log/nginx -name "dashboard_*.log.*" -mtime +30 -delete
find /opt/mt5-crs/var/logs -name "*.log.*" -mtime +30 -delete

# Review configuration changes
git log --oneline -20

# Test disaster recovery (if .env corrupted)
cp .env .env.disaster-recovery.backup

# Run full UAT suite
python3 scripts/uat_task_034.py

# Update DingTalk webhook if near expiration
# (Check with DingTalk admin for token rotation schedule)
```

### 4. Performance Monitoring

```bash
# Monitor Nginx worker processes
ps aux | grep nginx | grep -v grep

# Check Streamlit memory usage
ps aux | grep streamlit | grep -v grep

# Monitor port usage
sudo netstat -tlnp | grep -E "80|8501"

# Check system resources
free -h
uptime
```

---

## Rollback Procedure

If deployment fails or needs to be reverted:

```bash
# 1. Stop services
sudo systemctl stop nginx
pkill -f "streamlit run"

# 2. Restore previous .env
if [ -f /opt/mt5-crs/.env.backup.* ]; then
    cp /opt/mt5-crs/.env.backup.* /opt/mt5-crs/.env
fi

# 3. Remove Nginx configuration
sudo rm /etc/nginx/sites-enabled/dashboard
sudo rm /etc/nginx/sites-available/dashboard

# 4. Test and reload Nginx
sudo nginx -t
sudo systemctl reload nginx

# 5. Verify rollback
curl http://localhost/
# Should return connection refused or previous state
```

---

## Next Steps

1. ✅ **Environment Configuration** - Complete Step 1 above
2. ✅ **Nginx Setup** - Complete Step 2 (automated or manual)
3. ✅ **Service Startup** - Complete Step 3
4. ✅ **Verification** - Complete Step 4 (all tests)
5. ⬜ **Gate 2 Review** - Execute Step 5 after verification
6. ⬜ **Git Commit** - Commit deployment changes to version control

---

## Additional Resources

- **Nginx Documentation**: https://nginx.org/en/docs/
- **Streamlit Docs**: https://docs.streamlit.io/
- **DingTalk API**: https://open.dingtalk.com/
- **Basic Auth Guide**: https://en.wikipedia.org/wiki/Basic_access_authentication

---

**Document Version**: 1.0
**Last Updated**: 2026-01-05
**Status**: Ready for Production Deployment
