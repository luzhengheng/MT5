# Task #011.25: Remote Wake-Up & ZMQ Heartbeat Check
## Execution Guide

**Date**: 2025-12-31
**Protocol**: v2.2 (Docs-as-Code)
**Role**: DevOps Engineer
**Ticket**: #065
**Status**: 📋 **READY FOR EXECUTION**

---

## Executive Summary

This guide provides step-by-step instructions to remotely start the MT5/ZMQ Gateway on the Windows node (GTW) using the newly established SSH connection, and verify ZMQ data flow across the mesh.

**Prerequisites**:
- ✅ SSH mesh established (Task #011.20 completed)
- ✅ Password-less SSH to GTW working (`ssh gtw`)
- ✅ MT5 Gateway software already deployed on GTW
- ✅ ZMQ ports 5555/5556 currently closed (process stopped)

**Objective**: Turn the key and start the engine 🚗

---

## Current System State

### Known Facts (from previous tasks)

**Infrastructure Status**:
- ✅ INF (172.19.141.250): Linux control node, fully operational
- ✅ HUB (172.19.141.254): Linux hub, PostgreSQL + Redis running
- ✅ GPU (www.guangzhoupeak.com): Remote compute node, accessible
- ✅ GTW (172.19.141.255): Windows gateway, SSH accessible

**GTW Software Status**:
- ✅ MT5 Terminal installed (Terminal64.exe)
- ✅ ZMQ Gateway scripts deployed (`run_gateway.py` or similar)
- ❌ Gateway process currently stopped
- ❌ ZMQ ports 5555/5556 closed

### Expected After Execution

**GTW Process Status**:
- ✅ Python process running (`python.exe` or `Terminal64.exe`)
- ✅ ZMQ REQ port 5555 listening
- ✅ ZMQ SUB port 5556 listening
- ✅ Mesh verification shows 17/17 passed

---

## Execution Steps

### STEP 1: Locate Gateway Script on Windows

**Command** (from INF node):
```bash
# Search for Gateway script on GTW
ssh gtw "dir /s /b C:\*run_gateway.py C:\*gateway*.py C:\*zmq*.py 2>nul" | head -20
```

**Expected Output**:
```
C:\MT5_Gateway\run_gateway.py
C:\Users\Administrator\Documents\MT5_Scripts\gateway.py
# Or similar paths
```

**If not found**, try these common locations:
```bash
ssh gtw "dir C:\MT5_Gateway 2>nul"
ssh gtw "dir C:\Users\Administrator\Documents\MT5_Scripts 2>nul"
ssh gtw "dir C:\Program Files\MetaTrader 5 2>nul"
```

### STEP 2: Verify Python Installation on GTW

**Command**:
```bash
ssh gtw "python --version"
ssh gtw "where python"
```

**Expected Output**:
```
Python 3.9.x (or higher)
C:\Users\Administrator\AppData\Local\Programs\Python\Python39\python.exe
```

**If Python not in PATH**, use full path:
```bash
ssh gtw "C:\Users\Administrator\AppData\Local\Programs\Python\Python39\python.exe --version"
```

### STEP 3: Remote Start Gateway Process

**Option A: Background Process (Recommended)**:
```bash
# Start as background process using PowerShell
ssh gtw "powershell Start-Process python -ArgumentList 'C:\MT5_Gateway\run_gateway.py' -WindowStyle Hidden -PassThru | Select-Object Id"
```

**Expected Output**:
```
Id
--
1234  # Process ID
```

**Option B: Foreground (for testing)**:
```bash
# Start in foreground (blocks SSH session)
ssh gtw "cd C:\MT5_Gateway && python run_gateway.py"
# Press Ctrl+C to stop
```

**Option C: Windows Service** (if configured):
```bash
# Start as Windows Service
ssh gtw "sc start MT5Gateway"
# Or
ssh gtw "net start MT5Gateway"
```

### STEP 4: Verify Process Running

**Command**:
```bash
# Check if Python process is running
ssh gtw "tasklist /fi \"imagename eq python.exe\""
ssh gtw "tasklist /fi \"imagename eq Terminal64.exe\""
```

**Expected Output**:
```
Image Name                     PID Session Name        Session#    Mem Usage
========================= ======== ================ =========== ============
python.exe                    1234 Console                    1     45,678 K
```

**Check Process Details**:
```bash
# Get command line of running process
ssh gtw "wmic process where \"name='python.exe'\" get commandline"
```

**Expected**:
```
CommandLine
python.exe C:\MT5_Gateway\run_gateway.py
```

### STEP 5: Verify ZMQ Ports Listening

**Command**:
```bash
# Check if ports 5555 and 5556 are listening
ssh gtw "netstat -ano | findstr :5555"
ssh gtw "netstat -ano | findstr :5556"
```

**Expected Output**:
```
TCP    0.0.0.0:5555           0.0.0.0:0              LISTENING       1234
TCP    0.0.0.0:5556           0.0.0.0:0              LISTENING       1234
```

**If not listening**, check Gateway logs:
```bash
ssh gtw "type C:\MT5_Gateway\logs\gateway.log | more"
```

### STEP 6: Run Mesh Verification

**Command** (from INF node):
```bash
python3 scripts/ops_verify_mesh.py
```

**Expected Output** (ALL GREEN):
```
================================================================================
🔍 MESH VERIFICATION RESULTS
================================================================================

📋 [1/7] SSH CONNECTIVITY
✅ GTW SSH (172.19.141.255:22)        PASS    Connected
✅ HUB SSH (172.19.141.254:22)        PASS    Connected
✅ GPU SSH (www.guangzhoupeak.com:22) PASS    Connected

📋 [2/7] POSTGRESQL (HUB)
✅ PostgreSQL (172.19.141.254:5432)   PASS    Port open

📋 [3/7] REDIS (HUB)
✅ Redis (172.19.141.254:6379)        PASS    Port open

📋 [4/7] ZMQ GATEWAY (GTW)  ← Should turn GREEN
✅ GTW ZMQ REQ (172.19.141.255:5555)  PASS    Port open  ← Was RED
✅ GTW ZMQ SUB (172.19.141.255:5556)  PASS    Port open  ← Was RED

📋 [5/7] NETWORK CONNECTIVITY
✅ GTW ping (172.19.141.255)          PASS    <1ms
✅ HUB ping (172.19.141.254)          PASS    <1ms
✅ GPU ping (www.guangzhoupeak.com)   PASS    ~200ms

================================================================================
📊 MESH STATUS: 17/17 PASSED (100%)  ← Was 15/17 before
================================================================================
```

### STEP 7: ZMQ Heartbeat Test

**Create Test Script**:
```bash
cat > scripts/test_zmq_heartbeat.py << 'EOF'
#!/usr/bin/env python3
"""
Task #011.25: ZMQ Heartbeat Test
Test connectivity to GTW ZMQ Gateway by sending HEARTBEAT request
"""

import zmq
import json
import sys

# GTW ZMQ REQ endpoint
GTW_ZMQ_REQ = "tcp://172.19.141.255:5555"

def test_heartbeat():
    """Send HEARTBEAT to GTW and print response."""
    print(f"🔌 Connecting to GTW ZMQ REQ: {GTW_ZMQ_REQ}")

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout

    try:
        socket.connect(GTW_ZMQ_REQ)
        print(f"✅ Connected to {GTW_ZMQ_REQ}")

        # Send HEARTBEAT request
        request = {"action": "HEARTBEAT", "timestamp": int(time.time() * 1000)}
        print(f"\n📤 Sending request: {json.dumps(request, indent=2)}")
        socket.send_json(request)

        # Receive response
        print(f"⏳ Waiting for response (timeout: 5s)...")
        response = socket.recv_json()

        print(f"\n📥 Received response:")
        print(json.dumps(response, indent=2))

        # Validate response
        if response.get("status") == "OK" or "account" in response:
            print(f"\n✅ Heartbeat successful!")
            print(f"   Gateway is alive and responding")
            return True
        else:
            print(f"\n⚠️  Unexpected response format")
            return False

    except zmq.error.Again:
        print(f"\n❌ Timeout: No response from gateway (5s)")
        print(f"   Gateway may not be running or ZMQ port blocked")
        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

    finally:
        socket.close()
        context.term()

if __name__ == "__main__":
    import time
    success = test_heartbeat()
    sys.exit(0 if success else 1)
EOF

chmod +x scripts/test_zmq_heartbeat.py
```

**Run Test**:
```bash
python3 scripts/test_zmq_heartbeat.py
```

**Expected Output** (Success):
```
🔌 Connecting to GTW ZMQ REQ: tcp://172.19.141.255:5555
✅ Connected to tcp://172.19.141.255:5555

📤 Sending request: {
  "action": "HEARTBEAT",
  "timestamp": 1704000000000
}

⏳ Waiting for response (timeout: 5s)...

📥 Received response:
{
  "status": "OK",
  "gateway_version": "1.0.0",
  "uptime_seconds": 120,
  "account": {
    "login": 12345678,
    "server": "MetaQuotes-Demo",
    "balance": 10000.0
  }
}

✅ Heartbeat successful!
   Gateway is alive and responding
```

**Expected Output** (Failure - Gateway not running):
```
🔌 Connecting to GTW ZMQ REQ: tcp://172.19.141.255:5555
✅ Connected to tcp://172.19.141.255:5555

📤 Sending request: {
  "action": "HEARTBEAT",
  "timestamp": 1704000000000
}

⏳ Waiting for response (timeout: 5s)...

❌ Timeout: No response from gateway (5s)
   Gateway may not be running or ZMQ port blocked
```

---

## Troubleshooting

### Issue 1: Cannot Find Gateway Script

**Symptoms**:
```
ssh gtw "dir /s /b C:\*gateway*.py"
# No output
```

**Diagnosis**:
```bash
# Search all drives
ssh gtw "dir /s /b D:\*gateway*.py E:\*gateway*.py 2>nul"

# Check if MT5 is installed
ssh gtw "dir /s /b C:\*Terminal64.exe 2>nul"
```

**Solution**:
1. Gateway may be in different location
2. Contact user for actual installation path
3. Re-deploy Gateway if missing

### Issue 2: Python Not Found

**Symptoms**:
```
ssh gtw "python --version"
# 'python' is not recognized...
```

**Diagnosis**:
```bash
# Check Python installation
ssh gtw "dir /s /b C:\*python.exe 2>nul | findstr Python"
```

**Solution**:
```bash
# Use full path
ssh gtw "C:\Users\Administrator\AppData\Local\Programs\Python\Python39\python.exe --version"

# Or add to PATH (requires restart)
ssh gtw "setx PATH \"%PATH%;C:\Users\Administrator\AppData\Local\Programs\Python\Python39\""
```

### Issue 3: Process Starts but Exits Immediately

**Symptoms**:
```
# Process ID appears
ssh gtw "powershell Start-Process python ..."
Id: 1234

# But process not running
ssh gtw "tasklist /fi \"imagename eq python.exe\""
# No tasks running
```

**Diagnosis**:
```bash
# Check Gateway logs
ssh gtw "type C:\MT5_Gateway\logs\gateway.log | more"

# Check Windows Event Log
ssh gtw "powershell Get-EventLog -LogName Application -Newest 10 | Where-Object {$_.Source -like '*Python*'}"
```

**Common Causes**:
1. Missing dependencies (`pip install -r requirements.txt`)
2. Configuration error (check `config.json`)
3. MT5 not running (start Terminal64.exe first)
4. Permission denied (run as Administrator)

### Issue 4: Ports Not Listening

**Symptoms**:
```
ssh gtw "netstat -ano | findstr :5555"
# No output
```

**Diagnosis**:
```bash
# Check if process is running
ssh gtw "tasklist /fi \"imagename eq python.exe\""

# Check firewall
ssh gtw "netsh advfirewall firewall show rule name=all | findstr 5555"
```

**Solution**:
```bash
# Add firewall rule
ssh gtw "netsh advfirewall firewall add rule name=\"ZMQ REQ 5555\" dir=in action=allow protocol=TCP localport=5555"
ssh gtw "netsh advfirewall firewall add rule name=\"ZMQ SUB 5556\" dir=in action=allow protocol=TCP localport=5556"
```

### Issue 5: ZMQ Timeout

**Symptoms**:
```
python3 scripts/test_zmq_heartbeat.py
# ❌ Timeout: No response from gateway (5s)
```

**Diagnosis**:
```bash
# Test port connectivity
nc -zv 172.19.141.255 5555
# Or
telnet 172.19.141.255 5555

# Check if Gateway is processing requests
ssh gtw "type C:\MT5_Gateway\logs\gateway.log | findstr HEARTBEAT"
```

**Common Causes**:
1. Gateway process crashed (check logs)
2. ZMQ binding failed (port already in use)
3. MT5 Terminal not connected to broker
4. Firewall blocking (see Issue 4)

---

## Definition of Done

| Requirement | Status | Verification |
|------------|--------|--------------|
| Gateway script located | 🔄 | `ssh gtw "dir /s /b C:\*gateway*.py"` |
| Python verified | 🔄 | `ssh gtw "python --version"` |
| Gateway process started | 🔄 | `ssh gtw "powershell Start-Process..."` |
| Process running | 🔄 | `ssh gtw "tasklist /fi \"imagename eq python.exe\""` |
| Port 5555 listening | 🔄 | `ssh gtw "netstat -ano | findstr :5555"` |
| Port 5556 listening | 🔄 | `ssh gtw "netstat -ano | findstr :5556"` |
| Mesh verification 17/17 | 🔄 | `python3 scripts/ops_verify_mesh.py` |
| ZMQ heartbeat success | 🔄 | `python3 scripts/test_zmq_heartbeat.py` |

---

## Success Indicators

### Mesh Verification Output
```
📋 [4/7] ZMQ GATEWAY (GTW)
✅ GTW ZMQ REQ (172.19.141.255:5555)  PASS    Port open
✅ GTW ZMQ SUB (172.19.141.255:5556)  PASS    Port open

================================================================================
📊 MESH STATUS: 17/17 PASSED (100%)
================================================================================
```

### Heartbeat Test Output
```
✅ Heartbeat successful!
   Gateway is alive and responding
```

### Process Status
```
Image Name                     PID Session Name        Session#    Mem Usage
python.exe                    1234 Console                    1     45,678 K
```

---

## Next Steps After Completion

### 1. Continuous Operation

**Keep Gateway Running**:
```bash
# Option A: Windows Service (recommended)
# Already configured - will auto-start on boot

# Option B: Task Scheduler
# Schedule Gateway to run on startup

# Option C: Manual restart after reboot
ssh gtw "powershell Start-Process python -ArgumentList 'C:\MT5_Gateway\run_gateway.py' -WindowStyle Hidden"
```

### 2. Monitoring

**Check Gateway Health**:
```bash
# Daily health check
python3 scripts/ops_verify_mesh.py

# ZMQ heartbeat every 5 minutes
watch -n 300 'python3 scripts/test_zmq_heartbeat.py'
```

### 3. Integration Testing

**Test Full Data Flow**:
```bash
# Subscribe to market data
python3 scripts/test_zmq_subscribe.py  # To be created

# Send trade request
python3 scripts/test_zmq_trade.py  # To be created
```

---

## Command Reference

### Common Commands

**Check Gateway Status**:
```bash
# Process running?
ssh gtw "tasklist /fi \"imagename eq python.exe\""

# Ports listening?
ssh gtw "netstat -ano | findstr :555"

# Gateway logs
ssh gtw "type C:\MT5_Gateway\logs\gateway.log | more"
```

**Start/Stop Gateway**:
```bash
# Start
ssh gtw "powershell Start-Process python -ArgumentList 'C:\MT5_Gateway\run_gateway.py' -WindowStyle Hidden"

# Stop
ssh gtw "taskkill /f /im python.exe"

# Restart
ssh gtw "taskkill /f /im python.exe && powershell Start-Process python -ArgumentList 'C:\MT5_Gateway\run_gateway.py' -WindowStyle Hidden"
```

**Mesh Verification**:
```bash
# Full mesh check
python3 scripts/ops_verify_mesh.py

# ZMQ ports only
nc -zv 172.19.141.255 5555
nc -zv 172.19.141.255 5556
```

---

## Safety Notes

### Before Starting Gateway

1. **Verify MT5 Terminal Running**:
   ```bash
   ssh gtw "tasklist /fi \"imagename eq Terminal64.exe\""
   ```

2. **Check MT5 Connected to Broker**:
   - MT5 should show "Connected" status
   - Account should be logged in

3. **Backup Configuration**:
   ```bash
   ssh gtw "copy C:\MT5_Gateway\config.json C:\MT5_Gateway\config.json.backup"
   ```

### During Operation

1. **Monitor Resource Usage**:
   ```bash
   ssh gtw "wmic process where \"name='python.exe'\" get ProcessId,WorkingSetSize,CommandLine"
   ```

2. **Check Error Logs Regularly**:
   ```bash
   ssh gtw "type C:\MT5_Gateway\logs\gateway.log | findstr ERROR"
   ```

### After Completion

1. **Verify No Errors**:
   - Check Gateway logs for errors
   - Verify mesh verification 17/17 passed
   - Confirm heartbeat test succeeds

2. **Document Deployment**:
   - Record Gateway process ID
   - Note configuration settings
   - Document any issues encountered

---

## References

- [Task #011.20 Execution Guide](TASK_011_20_EXECUTION_GUIDE.md) - SSH mesh setup
- [ops_verify_mesh.py](../scripts/ops_verify_mesh.py) - Mesh verification script
- [ZMQ Documentation](https://zeromq.org/documentation/) - ZeroMQ protocol reference

---

**Status**: Ready for execution after SSH mesh is established
**Prerequisites**: Task #011.20 must be completed first
**Expected Duration**: 10-15 minutes
**Risk Level**: Low (read-only operations + safe process start)

**Next Task**: After Gateway is running, proceed with full integration testing

---

**Document Created**: 2025-12-31
**Protocol**: v2.2 (Docs-as-Code)
**Owner**: DevOps Engineer
**Ticket**: #065 (Task #011.25)

🎯 **READY TO TURN THE KEY AND START THE ENGINE**
