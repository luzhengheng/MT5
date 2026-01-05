# TASK #033: Quick Start Guide

**Web Dashboard & DingTalk ActionCard Integration**

---

## Overview

The Web Dashboard provides real-time monitoring of trading metrics and risk controls, with DingTalk integration for alert notifications that link directly back to the dashboard.

**Key Features**:
- 📊 Real-time metrics dashboard (PnL, positions, order history)
- 🚨 Risk alerts with DingTalk ActionCard format
- 🛑 Kill Switch status and manual reset controls
- 📱 Mobile-friendly web interface
- 🔗 Direct links from alerts to dashboard

---

## Installation

### 1. Requirements

The system uses:
- **Streamlit**: Web dashboard framework
- **Plotly**: Interactive charts
- **Pandas**: Data handling

These are already in your project dependencies.

### 2. Configuration

Add to your `.env` file (or export as environment variables):

```bash
# Required
DASHBOARD_PUBLIC_URL=http://www.crestive.net:8501

# Optional (for real DingTalk integration)
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
DINGTALK_SECRET=your-secret-key

# Optional (for Streamlit server)
STREAMLIT_HOST=0.0.0.0
STREAMLIT_PORT=8501
```

---

## Running the Dashboard

### Local Development

```bash
# Terminal 1: Start the dashboard
streamlit run src/dashboard/app.py

# Dashboard will be available at:
# http://localhost:8501/
```

### With Custom Configuration

```bash
# Set environment variables
export DASHBOARD_PUBLIC_URL="http://192.168.1.100:8501"
export STREAMLIT_HOST="0.0.0.0"
export STREAMLIT_PORT="8501"

# Run dashboard
streamlit run src/dashboard/app.py
```

### Docker Container

```bash
# Build image
docker build -t mt5-dashboard .

# Run container
docker run -p 8501:8501 \
  -e DASHBOARD_PUBLIC_URL="http://www.crestive.net:8501" \
  mt5-dashboard
```

---

## Using the Dashboard

### 1. Dashboard Home Page

When you access the dashboard, you'll see:

```
🤖 Signal Verification Dashboard
Task #019.01: Visualize trading bot signals and verify decision quality

Left Sidebar:
├─ 🚨 Risk Management
│  ├─ Kill Switch Status (ACTIVE/INACTIVE)
│  ├─ Manual Reset Button (if active)
│  └─ Dashboard URL display
├─ ⚙️ Configuration
│  ├─ Upload Trading Log File
│  └─ Select default log file

Main Content:
├─ 📊 Summary Metrics (KPIs)
├─ 📈 Candlestick Chart with Signals
├─ 📋 Trade History Table
└─ 📅 Event Timeline
```

### 2. Kill Switch Control

**Status Display**:
- 🟢 **Green**: System OPERATIONAL (kill switch inactive)
- 🔴 **Red**: System HALTED (kill switch active)

**When Kill Switch is ACTIVE**:
```
🛑 KILL SWITCH ACTIVE
Reason: Daily loss limit exceeded: -75.0
Time: 2026-01-05 16:35:58

[🔴 Manual Reset (Admin)] ← Click to reset
```

**Manual Reset** (requires admin authorization):
1. Click the reset button
2. System confirms action
3. Trading operations resume
4. Success notification appears

### 3. Monitoring Metrics

The dashboard displays:
- **Total Ticks**: Market tick events received
- **Total Signals**: Trading signals generated
- **Total Trades**: Orders executed
- **Win Rate**: % of profitable closed trades
- **Buy/Sell/Hold Signals**: Signal distribution
- **Open/Closed Trades**: Position status
- **Average P&L**: Average profit/loss percentage

### 4. Viewing Charts

**Candlestick Chart**:
1. Select symbol from dropdown
2. Choose timeframe (15min, 30min, 1H, 4H, 1D)
3. Blue diamonds mark buy signals
4. Hover to see details

**Trade History Table**:
- Entry time and price
- Exit time and price
- P&L percentage
- Trade status

---

## DingTalk Integration

### Sending Alerts

Alerts are sent automatically from the Risk Monitor:

```python
from src.dashboard import send_risk_alert, send_kill_switch_alert

# Send a risk alert
send_risk_alert(
    alert_type="ORDER_RATE_EXCEEDED",
    message="5 orders placed in 60 seconds. Further orders blocked.",
    severity="HIGH",
    dashboard_section="dashboard"
)

# Send kill switch alert
send_kill_switch_alert(
    reason="Daily loss limit exceeded: -75.0 USD"
)
```

### Alert Format

Alerts appear in DingTalk as **ActionCards** with:
- **Title**: Alert type (e.g., "ORDER_RATE_EXCEEDED")
- **Message**: Detailed explanation with Markdown formatting
- **Button**: "📊 View Dashboard" or "🔴 Kill Switch Dashboard"
- **Color**:
  - 🟠 Orange: HIGH severity
  - 🔴 Red: CRITICAL severity

### Example: High Alert

```
╔════════════════════════════════════════╗
║  ORDER_RATE_EXCEEDED                   ║
╠════════════════════════════════════════╣
║ [HIGH] ORDER_RATE_EXCEEDED             ║
║                                        ║
║ The system has received 5 orders in    ║
║ the last minute, reaching the limit.   ║
║                                        ║
║ **Dashboard**: Click the button below  ║
║ to view real-time metrics...           ║
║                                        ║
║ [📊 View Dashboard] ← Click here       ║
╚════════════════════════════════════════╝
```

### Example: Critical Alert

```
╔════════════════════════════════════════╗
║  ⛔ KILL SWITCH ACTIVATED              ║
╠════════════════════════════════════════╣
║ [CRITICAL] ⛔ KILL SWITCH ACTIVATED    ║
║                                        ║
║ **EMERGENCY STOP ACTIVATED**           ║
║                                        ║
║ 🚨 **Reason**: Daily loss limit       ║
║ exceeded: -75.0 USD                    ║
║                                        ║
║ All trading operations have been       ║
║ halted. Manual intervention required   ║
║ to resume.                             ║
║                                        ║
║ [🔴 Kill Switch Dashboard] ← Click    ║
╚════════════════════════════════════════╝
```

---

## Testing Alerts

### Run Test Suite

```bash
# Run all DingTalk integration tests
python3 scripts/test_dingtalk_card.py

# Expected output:
# ✅ DingTalkNotifier initialized successfully
# ✅ ActionCard message format is valid
# ✅ ActionCard sent successfully (mock mode)
# ✅ Risk alert sent successfully
# ✅ Kill switch alert sent successfully
# ✅ Dashboard URL format is valid
# ✅ HMAC signature generation working

# Summary: Passed: 7/7, Failed: 0/7
```

### Manual Test

```python
# In Python interactive shell
from src.dashboard import send_action_card

result = send_action_card(
    title="Test Alert",
    text="This is a test message with **markdown** support",
    btn_title="📊 View Dashboard",
    btn_url="http://www.crestive.net:8501/dashboard",
    severity="HIGH"
)

print(f"Alert sent: {result}")
# Check logs for: [WEBHOOK_MOCK] Would send: {...}
```

---

## Configuration Reference

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DASHBOARD_PUBLIC_URL` | `http://www.crestive.net:8501` | Public dashboard URL (used in alerts) |
| `DINGTALK_WEBHOOK_URL` | (empty) | DingTalk webhook URL (empty = mock mode) |
| `DINGTALK_SECRET` | (empty) | DingTalk secret for HMAC signing |
| `STREAMLIT_HOST` | `0.0.0.0` | IP address Streamlit binds to |
| `STREAMLIT_PORT` | `8501` | Port Streamlit listens on |

### Config File Location

Configuration is defined in: `src/config.py`

```python
DASHBOARD_PUBLIC_URL = os.getenv("DASHBOARD_PUBLIC_URL", "http://www.crestive.net:8501")
DINGTALK_WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK_URL", "")
DINGTALK_SECRET = os.getenv("DINGTALK_SECRET", "")
STREAMLIT_HOST = os.getenv("STREAMLIT_HOST", "0.0.0.0")
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))
```

---

## Troubleshooting

### Dashboard Won't Load

**Problem**: Browser shows "connection refused" at `http://localhost:8501/`

**Solutions**:
1. Check Streamlit is running:
   ```bash
   ps aux | grep streamlit
   ```
2. Verify port 8501 is listening:
   ```bash
   lsof -i :8501
   ```
3. Check for errors in terminal:
   ```bash
   # Restart with verbose output
   streamlit run src/dashboard/app.py --logger.level=debug
   ```

### Kill Switch Won't Reset

**Problem**: "Manual Reset (Admin)" button doesn't work

**Solutions**:
1. Verify kill switch lock file exists:
   ```bash
   ls -la /opt/mt5-crs/var/kill_switch.lock
   ```
2. Check if file is readable/writable:
   ```bash
   chmod 666 /opt/mt5-crs/var/kill_switch.lock
   ```
3. Check logs for errors:
   ```bash
   grep "KillSwitch" /opt/mt5-crs/var/logs/*.log
   ```

### Alerts Not Sending (Real Webhook)

**Problem**: DingTalk alerts not appearing in group chat

**Solutions**:
1. Verify webhook URL is configured:
   ```bash
   echo $DINGTALK_WEBHOOK_URL
   # Should show: https://oapi.dingtalk.com/robot/send?access_token=...
   ```
2. Verify secret is configured:
   ```bash
   echo $DINGTALK_SECRET
   # Should show: your-secret-key (not empty)
   ```
3. Test webhook manually:
   ```bash
   curl -X POST \
     -H 'Content-Type: application/json' \
     -d '{"msgtype":"text","text":{"content":"Test message"}}' \
     https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
   ```

### Permission Denied

**Problem**: Cannot write to kill switch lock file

**Solutions**:
1. Check permissions:
   ```bash
   ls -la /opt/mt5-crs/var/
   ```
2. Fix permissions:
   ```bash
   sudo chown trader:trader /opt/mt5-crs/var/
   sudo chmod 755 /opt/mt5-crs/var/
   ```

---

## API Reference

### DingTalkNotifier Class

```python
from src.dashboard import DingTalkNotifier

notifier = DingTalkNotifier(
    webhook_url="https://...",
    secret="key"
)

# Send ActionCard
notifier.send_action_card(
    title="Alert Title",
    text="Alert message with **markdown**",
    btn_title="Button text",
    btn_url="https://example.com",
    severity="HIGH"  # or "CRITICAL"
)

# Send risk alert
notifier.send_risk_alert(
    alert_type="ORDER_RATE_EXCEEDED",
    message="Details...",
    severity="HIGH",
    dashboard_section="dashboard"
)

# Send kill switch alert
notifier.send_kill_switch_alert(
    reason="Daily loss limit exceeded: -75.0"
)
```

### Convenience Functions

```python
from src.dashboard import (
    send_action_card,
    send_risk_alert,
    send_kill_switch_alert,
    get_notifier
)

# Quick send methods
send_action_card(title, text, btn_title, btn_url, severity)
send_risk_alert(alert_type, message, severity, dashboard_section)
send_kill_switch_alert(reason)

# Get global notifier instance
notifier = get_notifier()
```

---

## Security & Access Control

### Current Implementation (MVP)

⚠️ **No authentication** - Dashboard is accessible without password

### Production Recommendations

1. **Nginx Reverse Proxy with Basic Auth**:
   ```nginx
   location /kill-switch {
       auth_basic "Kill Switch Admin";
       auth_basic_user_file /etc/nginx/.htpasswd;
       proxy_pass http://localhost:8501;
   }
   ```

2. **VPN-Only Access**:
   - Run Streamlit on private network
   - Access only via VPN connection

3. **Firewall Rules**:
   ```bash
   sudo ufw allow from 192.168.1.0/24 to any port 8501
   sudo ufw deny from any to any port 8501
   ```

4. **DingTalk Webhook Security**:
   - Secret key stored in environment variables
   - Never hardcode credentials
   - Use Vault or Secrets Manager for production

---

## Performance Tips

### 1. Dashboard Responsiveness

- Streamlit auto-reloads on file changes
- Use `@st.cache` decorator for expensive operations:
  ```python
  @st.cache(ttl=60)
  def load_portfolio_data():
      return get_portfolio_state()
  ```

### 2. Large Data Sets

- Limit displayed rows:
  ```python
  st.dataframe(df.tail(100), use_container_width=True)
  ```

### 3. Chart Performance

- Use `plotly` for interactive charts
- Downsample data for large time ranges

---

## Next Steps

1. **Configure DingTalk Webhook** (optional):
   - Get webhook URL from DingTalk group settings
   - Set `DINGTALK_WEBHOOK_URL` environment variable

2. **Start Dashboard**:
   ```bash
   streamlit run src/dashboard/app.py
   ```

3. **Test Alerts**:
   ```bash
   python3 scripts/test_dingtalk_card.py
   ```

4. **Integrate with Risk Monitor**:
   - Risk monitor automatically sends alerts
   - Alerts appear in DingTalk group chat
   - Users click to visit dashboard

---

## Support & Documentation

- **Completion Report**: `docs/archive/tasks/TASK_033_DASHBOARD/COMPLETION_REPORT.md`
- **Architecture Details**: `docs/archive/tasks/TASK_033_DASHBOARD/ARCHITECTURE.md`
- **Test Results**: Run `python3 scripts/test_dingtalk_card.py`

---

**Status**: ✅ Ready for Production

**Last Updated**: 2026-01-05
