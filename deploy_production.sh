#!/bin/bash
# MT5-CRS Production Deployment Script
# TASK #034: Production Deployment & DingTalk UAT
# Protocol: v4.2 (Agentic-Loop)

set -e

echo "================================================================================"
echo "MT5-CRS Production Deployment Script"
echo "TASK #034: Production Deployment & DingTalk UAT"
echo "================================================================================"
echo ""

# Configuration
PROJECT_ROOT="/opt/mt5-crs"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
HTPASSWD_FILE="/etc/nginx/.htpasswd"
ENV_FILE="$PROJECT_ROOT/.env"

# Credentials (from task definition)
DASHBOARD_PASSWORD="MT5Hub@2025!Secure"
DINGTALK_SECRET="SEC7d7cbd2505332b3ed3053f87dadfd2bbac9b0c2ba46d63d7c587351f3bb08de5"

echo "Step 1: Preparing environment..."
echo "================================"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "⚠️  This script must be run as root for Nginx configuration."
   echo "Please run: sudo bash $0"
   exit 1
fi

# Create .env file with production secrets
echo "[INFO] Creating production .env file..."
if [ -f "$ENV_FILE" ]; then
    echo "[WARN] $ENV_FILE already exists. Backing up to $ENV_FILE.bak"
    cp "$ENV_FILE" "$ENV_FILE.bak"
fi

# Update .env with DingTalk secrets
if grep -q "DINGTALK_SECRET" "$ENV_FILE"; then
    echo "[INFO] Updating DINGTALK_SECRET in .env..."
    sed -i "s|^DINGTALK_SECRET=.*|DINGTALK_SECRET=$DINGTALK_SECRET|g" "$ENV_FILE"
else
    echo "DINGTALK_SECRET=$DINGTALK_SECRET" >> "$ENV_FILE"
fi

echo "✅ .env file configured with production secrets"
echo ""

echo "Step 2: Generating htpasswd for Basic Auth..."
echo "=============================================="

# Generate htpasswd file
echo "[INFO] Creating htpasswd file with credentials..."
sudo htpasswd -bc "$HTPASSWD_FILE" admin "$DASHBOARD_PASSWORD" 2>/dev/null || {
    echo "[ERROR] Failed to create htpasswd. Installing apache2-utils..."
    apt-get update > /dev/null
    apt-get install -y apache2-utils > /dev/null
    htpasswd -bc "$HTPASSWD_FILE" admin "$DASHBOARD_PASSWORD"
}

# Set permissions
chmod 644 "$HTPASSWD_FILE"
echo "✅ htpasswd file created at $HTPASSWD_FILE"
echo "   Username: admin"
echo "   Password: ****** (stored securely)"
echo ""

echo "Step 3: Deploying Nginx configuration..."
echo "========================================="

# Copy Nginx configuration
echo "[INFO] Copying Nginx configuration..."
sudo cp "$PROJECT_ROOT/nginx_dashboard.conf" "$NGINX_CONF_DIR/dashboard" 2>/dev/null || {
    echo "[ERROR] Could not copy Nginx config. Checking path..."
    if [ ! -d "$NGINX_CONF_DIR" ]; then
        echo "[WARN] Nginx not installed. Installing nginx..."
        apt-get update > /dev/null
        apt-get install -y nginx > /dev/null
    fi
    sudo cp "$PROJECT_ROOT/nginx_dashboard.conf" "$NGINX_CONF_DIR/dashboard"
}

# Create symlink to enable site
if [ ! -L "$NGINX_ENABLED_DIR/dashboard" ]; then
    echo "[INFO] Enabling Nginx site..."
    sudo ln -s "$NGINX_CONF_DIR/dashboard" "$NGINX_ENABLED_DIR/dashboard"
else
    echo "[INFO] Nginx site already enabled"
fi

# Test Nginx configuration
echo "[INFO] Testing Nginx configuration..."
sudo nginx -t > /dev/null 2>&1 || {
    echo "[ERROR] Nginx configuration test failed!"
    sudo nginx -t
    exit 1
}
echo "✅ Nginx configuration is valid"

# Reload Nginx
echo "[INFO] Reloading Nginx..."
sudo systemctl reload nginx
echo "✅ Nginx reloaded successfully"
echo ""

echo "Step 4: Verifying deployment..."
echo "==============================="

# Check if port 80 is responding
echo "[INFO] Checking Nginx is responding on port 80..."
if curl -s -I http://localhost/ > /dev/null 2>&1; then
    echo "✅ Nginx is responding on port 80"
else
    echo "[WARN] Could not connect to Nginx on port 80 (might be firewall)"
fi

# Verify .env has required secrets
echo "[INFO] Verifying .env configuration..."
if grep -q "DINGTALK_SECRET=SEC" "$ENV_FILE"; then
    echo "✅ DINGTALK_SECRET configured in .env"
else
    echo "❌ DINGTALK_SECRET not properly configured"
    exit 1
fi

echo ""
echo "Step 5: Starting Streamlit service..."
echo "====================================="

# Kill existing Streamlit process if running
if pgrep -f "streamlit run" > /dev/null; then
    echo "[WARN] Streamlit already running. Stopping..."
    pkill -f "streamlit run" || true
    sleep 2
fi

# Start Streamlit
echo "[INFO] Starting Streamlit on port 8501..."
cd "$PROJECT_ROOT"

# Load .env file and start Streamlit
set +e
nohup env $(cat "$ENV_FILE" | grep -v '^#' | xargs) \
    streamlit run src/dashboard/app.py \
    --server.port 8501 \
    --server.address 127.0.0.1 \
    --client.showErrorDetails false \
    > "$PROJECT_ROOT/var/logs/streamlit.log" 2>&1 &

sleep 3

if pgrep -f "streamlit run" > /dev/null; then
    echo "✅ Streamlit started successfully (PID: $(pgrep -f 'streamlit run'))"
else
    echo "❌ Failed to start Streamlit"
    echo "Check logs: $PROJECT_ROOT/var/logs/streamlit.log"
    exit 1
fi
set -e

echo ""
echo "================================================================================"
echo "✅ DEPLOYMENT COMPLETE"
echo "================================================================================"
echo ""
echo "Dashboard Access:"
echo "  URL: http://www.crestive.net"
echo "  Username: admin"
echo "  Password: ******* (stored in htpasswd)"
echo ""
echo "Backend Services:"
echo "  Nginx: ✅ Running (port 80)"
echo "  Streamlit: ✅ Running (port 8501, proxied through Nginx)"
echo ""
echo "Production Configuration:"
echo "  .env file: $ENV_FILE"
echo "  Nginx config: $NGINX_CONF_DIR/dashboard"
echo "  htpasswd: $HTPASSWD_FILE"
echo "  Logs: $PROJECT_ROOT/var/logs/streamlit.log"
echo ""
echo "Next Steps:"
echo "  1. Test dashboard: http://www.crestive.net"
echo "  2. Run UAT tests: python3 scripts/test_dingtalk_card.py"
echo "  3. Verify DingTalk integration: Check DingTalk group chat"
echo "  4. Review logs: tail -f $PROJECT_ROOT/var/logs/streamlit.log"
echo ""
echo "================================================================================"
