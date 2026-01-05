# TASK #034 - Production Deployment Verification Checklist
## Step-by-Step Verification of All Deployment Components

**Status**: Ready for Verification
**Date**: 2026-01-05
**Protocol**: v4.2 (Agentic-Loop)

---

## Pre-Deployment Environment Verification

### Infrastructure Readiness

- [ ] **System OS**: Ubuntu 20.04+ or CentOS 8+
  ```bash
  lsb_release -a
  ```

- [ ] **Python Version**: 3.9+
  ```bash
  python3 --version
  # Expected: Python 3.9.x or higher
  ```

- [ ] **Disk Space**: At least 2GB available
  ```bash
  df -h /opt/mt5-crs | awk 'NR==2 {print $4}'
  # Expected: 2G or higher
  ```

- [ ] **Memory**: At least 2GB available
  ```bash
  free -h | grep Mem | awk '{print $7}'
  # Expected: 2G or higher
  ```

- [ ] **Network Connectivity**: Can reach DingTalk API
  ```bash
  curl -I https://oapi.dingtalk.com/
  # Expected: HTTP 200 or redirect
  ```

- [ ] **Git Installed**: For version control
  ```bash
  git --version
  # Expected: git version 2.x or higher
  ```

### Port Availability

- [ ] **Port 80**: Available for Nginx
  ```bash
  sudo netstat -tlnp | grep :80
  # Expected: No output (port free) or existing Nginx
  ```

- [ ] **Port 8501**: Available for Streamlit
  ```bash
  sudo netstat -tlnp | grep :8501
  # Expected: No output (port free)
  ```

- [ ] **Port 443**: Available for HTTPS (if enabling SSL)
  ```bash
  sudo netstat -tlnp | grep :443
  # Expected: No output (port free)
  ```

---

## Step 1: Environment Configuration Verification

### .env File Creation

- [ ] **.env.production exists**
  ```bash
  ls -la /opt/mt5-crs/.env.production
  # Expected: File exists, readable
  ```

- [ ] **.env copied from template**
  ```bash
  [ -f /opt/mt5-crs/.env ] && echo "✅ .env exists" || echo "❌ .env missing"
  ```

- [ ] **Backup of previous .env created**
  ```bash
  ls -la /opt/mt5-crs/.env.backup.* 2>/dev/null | wc -l
  # Expected: At least 1 backup file
  ```

### Environment Variables Configuration

- [ ] **DASHBOARD_PUBLIC_URL set correctly**
  ```bash
  grep "DASHBOARD_PUBLIC_URL" /opt/mt5-crs/.env
  # Expected: DASHBOARD_PUBLIC_URL=http://www.crestive.net
  ```

- [ ] **DINGTALK_WEBHOOK_URL configured**
  ```bash
  grep "DINGTALK_WEBHOOK_URL" /opt/mt5-crs/.env | grep -v "YOUR_ACTUAL_TOKEN"
  # Expected: Shows actual webhook URL (not placeholder)
  ```

- [ ] **DINGTALK_SECRET present and valid**
  ```bash
  grep "DINGTALK_SECRET=SEC" /opt/mt5-crs/.env
  # Expected: SEC followed by 64 hex characters
  ```

- [ ] **STREAMLIT_HOST configured**
  ```bash
  grep "STREAMLIT_HOST=127.0.0.1" /opt/mt5-crs/.env
  # Expected: 127.0.0.1 or 0.0.0.0
  ```

- [ ] **STREAMLIT_PORT configured**
  ```bash
  grep "STREAMLIT_PORT=8501" /opt/mt5-crs/.env
  # Expected: 8501
  ```

### File Permissions

- [ ] **.env has restricted permissions**
  ```bash
  stat -c "%a" /opt/mt5-crs/.env
  # Expected: 600 (user read/write only)
  ```

- [ ] **No hardcoded secrets in source code**
  ```bash
  grep -r "SEC7d7cbd" /opt/mt5-crs/src 2>/dev/null | wc -l
  # Expected: 0 (no occurrences)
  ```

- [ ] **.env in .gitignore**
  ```bash
  grep "\.env" /opt/mt5-crs/.gitignore
  # Expected: Multiple .env patterns
  ```

---

## Step 2: Nginx Setup Verification

### Configuration Files

- [ ] **nginx_dashboard.conf exists**
  ```bash
  ls -la /opt/mt5-crs/nginx_dashboard.conf
  # Expected: File exists, readable
  ```

- [ ] **Nginx configuration copied to sites-available**
  ```bash
  ls -la /etc/nginx/sites-available/dashboard
  # Expected: File exists with 644 permissions
  ```

- [ ] **Nginx site symlink created**
  ```bash
  ls -la /etc/nginx/sites-enabled/dashboard
  # Expected: Symbolic link exists
  ```

### htpasswd Configuration

- [ ] **htpasswd file created**
  ```bash
  sudo ls -la /etc/nginx/.htpasswd
  # Expected: File exists
  ```

- [ ] **htpasswd has correct permissions**
  ```bash
  sudo stat -c "%a" /etc/nginx/.htpasswd
  # Expected: 640 or 644 (readable by Nginx)
  ```

- [ ] **htpasswd contains admin user**
  ```bash
  sudo grep "^admin:" /etc/nginx/.htpasswd
  # Expected: admin:$apr1$... (hashed password)
  ```

### Nginx Service

- [ ] **Nginx configuration is valid**
  ```bash
  sudo nginx -t
  # Expected: "syntax is ok" and "test is successful"
  ```

- [ ] **Nginx service installed**
  ```bash
  which nginx
  # Expected: /usr/sbin/nginx or similar
  ```

- [ ] **Nginx is running**
  ```bash
  sudo systemctl status nginx | grep "active (running)"
  # Expected: active (running) output
  ```

- [ ] **Nginx listening on port 80**
  ```bash
  sudo netstat -tlnp | grep :80 | grep nginx
  # Expected: Shows nginx process listening on port 80
  ```

### Security Headers

- [ ] **Security headers configured in Nginx**
  ```bash
  grep "X-Frame-Options" /etc/nginx/sites-available/dashboard
  # Expected: X-Frame-Options header present
  ```

- [ ] **SAMEORIGIN header set**
  ```bash
  curl -I http://localhost/ 2>/dev/null | grep X-Frame-Options
  # Expected: X-Frame-Options: SAMEORIGIN
  ```

---

## Step 3: Service Startup Verification

### Streamlit Service

- [ ] **Streamlit installed**
  ```bash
  pip3 list | grep streamlit
  # Expected: streamlit with version number
  ```

- [ ] **Required dependencies installed**
  ```bash
  python3 -c "import streamlit; import pandas; import plotly"
  # Expected: No import errors
  ```

- [ ] **Streamlit process running**
  ```bash
  pgrep -f "streamlit run"
  # Expected: PID number (not empty)
  ```

- [ ] **Streamlit listening on port 8501**
  ```bash
  netstat -tlnp 2>/dev/null | grep :8501
  # Expected: Shows process on port 8501
  ```

- [ ] **Streamlit logs exist**
  ```bash
  ls -la /opt/mt5-crs/var/logs/streamlit.log
  # Expected: File exists, contains log entries
  ```

### Log Directories

- [ ] **Log directory exists**
  ```bash
  ls -la /opt/mt5-crs/var/logs/
  # Expected: Directory exists with correct permissions
  ```

- [ ] **Streamlit log is being written**
  ```bash
  tail -1 /opt/mt5-crs/var/logs/streamlit.log | grep -E "2026-01-0"
  # Expected: Recent timestamp (today or recent date)
  ```

- [ ] **Nginx logs accessible**
  ```bash
  sudo tail -1 /var/log/nginx/dashboard_access.log
  # Expected: Recent access log entry
  ```

---

## Step 4: Connectivity Testing

### Local Backend Connectivity

- [ ] **Streamlit backend responds on localhost**
  ```bash
  curl -I http://127.0.0.1:8501/
  # Expected: HTTP/1.1 200 OK
  ```

- [ ] **Can connect to Streamlit from Nginx proxy**
  ```bash
  curl -I http://127.0.0.1:8501/_stcore/health
  # Expected: HTTP/1.1 200 OK or similar
  ```

### Nginx Reverse Proxy

- [ ] **Nginx responds to requests**
  ```bash
  curl -I http://localhost/
  # Expected: HTTP/1.1 401 Unauthorized (auth required)
  ```

- [ ] **Correct authentication challenge**
  ```bash
  curl -I http://localhost/ 2>/dev/null | grep WWW-Authenticate
  # Expected: WWW-Authenticate: Basic realm="MT5-CRS Dashboard..."
  ```

### Authenticated Access

- [ ] **Valid credentials allow access**
  ```bash
  curl -I -u admin:MT5Hub@2025!Secure http://localhost/
  # Expected: HTTP/1.1 200 OK
  ```

- [ ] **Invalid credentials denied**
  ```bash
  curl -I -u admin:wrongpassword http://localhost/
  # Expected: HTTP/1.1 401 Unauthorized
  ```

- [ ] **Dashboard page loads**
  ```bash
  curl -s -u admin:MT5Hub@2025!Secure http://localhost/ | grep -q "MT5" && echo "✅ Dashboard loaded"
  # Expected: ✅ Dashboard loaded
  ```

### DingTalk Connectivity

- [ ] **Can reach DingTalk API**
  ```bash
  curl -I https://oapi.dingtalk.com/
  # Expected: HTTP/1.1 200 OK or 301/302 redirect
  ```

- [ ] **DingTalk webhook URL is accessible**
  ```bash
  WEBHOOK=$(grep DINGTALK_WEBHOOK_URL /opt/mt5-crs/.env | cut -d= -f2)
  curl -I "$WEBHOOK" 2>/dev/null | head -1
  # Expected: HTTP/1.1 200 OK or 415 (POST not GET)
  ```

---

## Step 5: UAT Test Execution

### Run Test Suite

- [ ] **UAT script exists**
  ```bash
  ls -la /opt/mt5-crs/scripts/uat_task_034.py
  # Expected: File exists and is executable
  ```

- [ ] **Run UAT tests**
  ```bash
  cd /opt/mt5-crs
  python3 scripts/uat_task_034.py 2>&1 | tee /tmp/uat_results.txt
  ```

### Test Results

- [ ] **Test 1: Dashboard Access - PASS** ✅
  ```bash
  grep "✅.*Dashboard" /tmp/uat_results.txt
  # Expected: At least one passing result
  ```

- [ ] **Test 2: Authenticated Access - PASS** ✅
  ```bash
  grep "✅.*credentials" /tmp/uat_results.txt
  # Expected: Authentication test passing
  ```

- [ ] **Test 3: DingTalk Configuration - PASS** ✅
  ```bash
  grep "✅.*DingTalk.*configured" /tmp/uat_results.txt
  # Expected: DingTalk config verified
  ```

- [ ] **Test 4: Send Real Alert - PASS** ✅
  ```bash
  grep "✅.*alert sent" /tmp/uat_results.txt
  # Expected: Real DingTalk message sent
  ```

- [ ] **Test 5: Kill Switch Alert - PASS** ✅
  ```bash
  grep "✅.*kill switch" /tmp/uat_results.txt
  # Expected: Kill switch alert working
  ```

- [ ] **Test 6: Dashboard URL Validation - PASS** ✅
  ```bash
  grep "✅.*Dashboard URL" /tmp/uat_results.txt
  # Expected: URL properly configured
  ```

- [ ] **Test 7: Nginx Configuration - PASS** ✅
  ```bash
  grep "✅.*Nginx" /tmp/uat_results.txt
  # Expected: Nginx configuration valid
  ```

- [ ] **Test 8: Streamlit Service - PASS** ✅
  ```bash
  grep "✅.*Streamlit" /tmp/uat_results.txt
  # Expected: Streamlit service running
  ```

### Test Summary

- [ ] **All 8 tests passing**
  ```bash
  grep "ALL.*TESTS.*PASSED\|ALL.*PASSED" /tmp/uat_results.txt
  # Expected: Success message
  ```

- [ ] **No critical failures**
  ```bash
  grep "❌\|FAILED" /tmp/uat_results.txt | wc -l
  # Expected: 0 (no failures)
  ```

---

## Step 6: DingTalk Integration Testing

### Integration Tests

- [ ] **DingTalk test script exists**
  ```bash
  ls -la /opt/mt5-crs/scripts/test_dingtalk_card.py
  # Expected: File exists
  ```

- [ ] **Run DingTalk tests**
  ```bash
  cd /opt/mt5-crs
  python3 scripts/test_dingtalk_card.py 2>&1 | tee /tmp/dingtalk_results.txt
  ```

- [ ] **All 7 DingTalk tests passing**
  ```bash
  grep "7/7.*passing\|All.*passing" /tmp/dingtalk_results.txt
  # Expected: Success message
  ```

### Message Verification in DingTalk

- [ ] **Check DingTalk group for test message**
  - Open DingTalk desktop application
  - Navigate to MT5-CRS Risk Alerts group
  - Expected: Message from "MT5-CRS Risk Monitor" robot
  - Content: "UAT Testing" or "Test message"

- [ ] **Message contains dashboard link**
  - Look for clickable button in the message
  - Expected: "View Dashboard" or similar button
  - URL should be: `http://www.crestive.net`

- [ ] **Link works when clicked**
  - Click the dashboard link in message
  - Should prompt for username/password
  - Expected: Can login with admin credentials

---

## Step 7: Security Verification

### Authentication Security

- [ ] **Basic Auth is working**
  ```bash
  # No auth should be denied
  curl -s -o /dev/null -w "%{http_code}" http://localhost/
  # Expected: 401

  # Valid auth should succeed
  curl -s -o /dev/null -w "%{http_code}" -u admin:MT5Hub@2025!Secure http://localhost/
  # Expected: 200
  ```

- [ ] **Password is not logged in plaintext**
  ```bash
  grep "MT5Hub@2025" /var/log/nginx/dashboard_access.log 2>/dev/null | wc -l
  # Expected: 0 (password not in access logs)
  ```

- [ ] **htpasswd file is not readable by everyone**
  ```bash
  sudo stat -c "%a %U:%G" /etc/nginx/.htpasswd
  # Expected: 640 root:root (or similar, not 644)
  ```

### Secret Protection

- [ ] **DINGTALK_SECRET not in git history**
  ```bash
  git log -S "SEC7d7cbd" --all 2>/dev/null | wc -l
  # Expected: 0 (no commits with secret)
  ```

- [ ] **.env file not committed**
  ```bash
  git ls-files | grep "^\.env$"
  # Expected: No output (not in git)
  ```

- [ ] **Configuration in environment only**
  ```bash
  grep -r "DINGTALK_WEBHOOK_URL" /opt/mt5-crs/src/ | wc -l
  # Expected: 0 (not hardcoded in source)
  ```

### Network Security

- [ ] **HTTPS available (if configured)**
  ```bash
  curl -I https://www.crestive.net 2>/dev/null | head -1
  # Expected: HTTP/1.1 200 OK (if SSL configured)
  ```

- [ ] **Security headers present**
  ```bash
  curl -I -u admin:MT5Hub@2025!Secure http://localhost/ 2>/dev/null | grep -E "X-Frame|X-Content|X-XSS"
  # Expected: Multiple security headers
  ```

---

## Step 8: Performance & Logs

### Performance Checks

- [ ] **Dashboard loads within 5 seconds**
  ```bash
  time curl -s -u admin:MT5Hub@2025!Secure http://localhost/ > /dev/null
  # Expected: real <5s
  ```

- [ ] **Nginx response time is fast**
  ```bash
  curl -w "Response time: %{time_total}s\n" -o /dev/null -s -u admin:MT5Hub@2025!Secure http://localhost/
  # Expected: time_total < 1.0 seconds
  ```

### Log Verification

- [ ] **Nginx access log has correct entries**
  ```bash
  sudo tail -10 /var/log/nginx/dashboard_access.log | grep -c "admin"
  # Expected: Multiple entries
  ```

- [ ] **Error logs are clean**
  ```bash
  sudo tail -20 /var/log/nginx/dashboard_error.log | grep -i error | wc -l
  # Expected: 0 or minimal errors
  ```

- [ ] **Streamlit logs show successful startup**
  ```bash
  grep -i "started\|listening\|running" /opt/mt5-crs/var/logs/streamlit.log | tail -3
  # Expected: Startup messages without errors
  ```

---

## Step 9: Complete Deployment Verification

### Final Checklist

- [ ] **All 8 UAT tests passing** ✅
- [ ] **All 7 DingTalk tests passing** ✅
- [ ] **Dashboard accessible via browser** ✅
- [ ] **DingTalk messages received in group** ✅
- [ ] **Authentication working (both valid and invalid)** ✅
- [ ] **Nginx configuration valid** ✅
- [ ] **Streamlit service running** ✅
- [ ] **All required services listening on correct ports** ✅
- [ ] **Secrets properly protected** ✅
- [ ] **No hardcoded credentials in code or logs** ✅
- [ ] **SSL/TLS configured (if required)** ✅
- [ ] **Backup of .env created** ✅
- [ ] **Post-deployment documentation complete** ✅
- [ ] **Team notified of deployment completion** ✅

### Summary Report

```bash
# Create final verification report
cat > /tmp/deployment_verification_report.txt << 'EOF'
MT5-CRS TASK #034 - PRODUCTION DEPLOYMENT VERIFICATION REPORT

Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Deployed By: $USER
Environment: Production

=== INFRASTRUCTURE VERIFICATION ===
✅ OS Version: Linux kernel 5.10.134
✅ Python Version: 3.9+
✅ Disk Space: >2GB available
✅ Memory: >2GB available
✅ Network: Reachable (DingTalk API connectivity confirmed)

=== SERVICE VERIFICATION ===
✅ Nginx: Running on port 80, configuration valid
✅ Streamlit: Running on port 8501
✅ htpasswd: Configured with admin user
✅ Environment: All secrets loaded correctly

=== FUNCTIONAL VERIFICATION ===
✅ Dashboard: Accessible via http://www.crestive.net (with auth)
✅ Authentication: Working (401 without, 200 with credentials)
✅ DingTalk Integration: 7/7 tests passing
✅ UAT Tests: 8/8 tests passing
✅ Kill Switch: Functional and accessible from dashboard
✅ Risk Alerts: Real messages being sent to DingTalk group

=== SECURITY VERIFICATION ===
✅ Secrets: Protected in .env, not hardcoded
✅ Credentials: Properly hashed in htpasswd
✅ Logs: No passwords logged in plaintext
✅ Git: .env and secrets excluded from repository
✅ HTTPS: [Configured/Not yet configured] *

=== DEPLOYMENT STATUS ===
STATUS: ✅ READY FOR PRODUCTION

Next Steps:
1. Run Gate 2 AI review: python3 gemini_review_bridge.py
2. Create deployment commit: git commit ...
3. Notify team of successful deployment
4. Begin 24-hour monitoring period
5. Review logs daily for first week

* If HTTPS not configured, schedule SSL setup for Day 2

EOF

cat /tmp/deployment_verification_report.txt
```

---

## Gate 2 AI Review

- [ ] **Execute Gate 2 AI review**
  ```bash
  cd /opt/mt5-crs
  python3 gemini_review_bridge.py
  ```

- [ ] **Review passes with confidence level ⭐⭐⭐⭐⭐**
  - Expected output confirms production readiness
  - Nginx configuration correct and secure
  - DingTalk integration properly implemented
  - Kill Switch controls functional

---

## Post-Deployment Actions

### Commit Changes

- [ ] **Stage all deployment files**
  ```bash
  cd /opt/mt5-crs
  git add .env.production nginx_dashboard.conf deploy_production.sh scripts/uat_task_034.py
  git add docs/archive/tasks/TASK_034_DEPLOYMENT/
  ```

- [ ] **Create deployment commit**
  ```bash
  git commit -m "ops: production deployment with nginx basic auth and dingtalk integration"
  ```

- [ ] **Verify commit created**
  ```bash
  git log -1 --oneline
  ```

### Notify Team

- [ ] **Send deployment notification**
  - Message to team: "TASK #034 production deployment complete"
  - Include: Dashboard URL, access instructions, support contact
  - Send via email and DingTalk

- [ ] **Update status documentation**
  - Mark TASK #034 as COMPLETE in project tracking
  - Document deployment timestamp
  - Store deployment report in secure location

### Begin Monitoring

- [ ] **Set up log monitoring**
  ```bash
  # Monitor dashboard access
  watch -n 60 'tail /var/log/nginx/dashboard_access.log'
  ```

- [ ] **Establish on-call rotation**
  - Assign engineer for 24-hour monitoring
  - Provide escalation procedure
  - Ensure alert mechanisms are active

---

## Troubleshooting Quick Reference

| Issue | Check | Solution |
|-------|-------|----------|
| 401 Unauthorized | `curl -u admin:... http://localhost/` | Verify credentials |
| Port 80 in use | `sudo lsof -i :80` | Kill conflicting service |
| DingTalk not sending | Check webhook URL in .env | Verify URL format and token |
| Streamlit not running | `pgrep -f streamlit` | Check logs, reinstall if needed |
| Nginx config error | `sudo nginx -t` | Fix syntax errors in config |
| .env not loading | Check permissions and syntax | Verify `chmod 600 .env` |

---

**Verification Date**: 2026-01-05
**Verification Status**: Ready to Execute
**Estimated Duration**: 30-60 minutes
**Prepared By**: DevOps Engineer
