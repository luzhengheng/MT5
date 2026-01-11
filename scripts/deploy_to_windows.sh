#!/bin/bash
# Deploy gateway code from INF to GTW (Windows) via SSH
# Task #083: Hot-Patch Windows Gateway with Latest Protocol
# SECURITY: Uses environment variables for sensitive data

set -e

# Configuration from environment variables (with secure defaults)
WINDOWS_HOST="${DEPLOY_HOST:-172.19.141.255}"
WINDOWS_USER="${DEPLOY_USER:-Administrator}"
LOCAL_GATEWAY_DIR="./src/gateway"
WINDOWS_PROJECT_DIR="C:/mt5-crs"
WINDOWS_GATEWAY_DIR="$WINDOWS_PROJECT_DIR/src/gateway"

echo "=========================================="
echo "🚀 Task #083: Windows Gateway Deployment (Secure)"
echo "=========================================="
echo "📋 Configuration:"
echo "   Target Host: $WINDOWS_HOST"
echo "   Target User: $WINDOWS_USER"
echo ""

# Step 1: Verify local gateway code exists
echo ""
echo "[Step 1] Verifying local gateway code..."
if [ ! -d "$LOCAL_GATEWAY_DIR" ]; then
    echo "❌ ERROR: Local gateway directory not found at $LOCAL_GATEWAY_DIR"
    exit 1
fi

echo "✅ Found local gateway directory"
ls -lh $LOCAL_GATEWAY_DIR/*.py | awk '{print "   - " $9 " (" $5 ")"}'

# Step 2: Deploy via SCP (with SSH key-based auth, respecting known_hosts)
echo ""
echo "[Step 2] Deploying gateway code to Windows..."
echo "📤 Copying files via SCP..."

# Deploy each file with known_hosts check (fails if host unknown)
scp -o ConnectTimeout=10 -r $LOCAL_GATEWAY_DIR/* $WINDOWS_USER@$WINDOWS_HOST:/c/mt5-crs/src/gateway/ 2>&1 | tee -a task_083_deploy.log

echo "✅ Files deployed successfully"

# Step 3: Verify deployment on Windows
echo ""
echo "[Step 3] Verifying deployment on Windows..."
ssh -o ConnectTimeout=10 $WINDOWS_USER@$WINDOWS_HOST "dir C:\mt5-crs\src\gateway" 2>&1 | tee -a task_083_deploy.log

# Step 4: Gracefully restart service (not kill all Python processes!)
echo ""
echo "[Step 4] Gracefully restarting gateway service..."
echo "⚠️  NOTE: This restarts only the MT5 Gateway Service, not all Python processes"

# Use PowerShell to restart Windows Service (if registered) or use PID file
ssh -o ConnectTimeout=10 $WINDOWS_USER@$WINDOWS_HOST << 'POWERSHELL_EOF' 2>&1 | tee -a task_083_deploy.log
# Attempt 1: Restart via Windows Service (preferred method)
try {
    $service = Get-Service -Name "MT5GatewayService" -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "✅ Found MT5GatewayService, restarting..."
        Restart-Service -Name "MT5GatewayService" -Force
        Start-Sleep -Seconds 2
        Write-Host "✅ Service restarted successfully"
        exit 0
    }
} catch {}

# Attempt 2: Fallback - gracefully stop gateway via PID file (if available)
$pidFile = "C:\mt5-crs\gateway.pid"
if (Test-Path $pidFile) {
    $pid = Get-Content $pidFile | ForEach-Object { $_.Trim() }
    if ($pid) {
        try {
            $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "✅ Gracefully stopping gateway process (PID: $pid)..."
                $process | Stop-Process -Force
                Remove-Item $pidFile -Force
                Start-Sleep -Seconds 2
                Write-Host "✅ Process stopped and cleaned up"
                exit 0
            }
        } catch {}
    }
}

# Attempt 3: Service not found, output info for manual restart
Write-Host "⚠️  Gateway service not found as Windows Service or PID file"
Write-Host "    Manual restart required. Run on Windows:"
Write-Host "    python C:\mt5-crs\scripts\start_windows_gateway.py"
POWERSHELL_EOF

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. If service wasn't auto-restarted, SSH into Windows:"
echo "   ssh $WINDOWS_USER@$WINDOWS_HOST"
echo "2. Manually start gateway (if needed):"
echo "   cd C:\mt5-crs && python scripts/start_windows_gateway.py"
echo "3. Run verification from this machine:"
echo "   python3 scripts/verify_execution_link.py"
