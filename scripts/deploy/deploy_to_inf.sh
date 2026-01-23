#!/bin/bash
set -e
INF_IP="172.19.141.250"
LOG_FILE="logs/deploy.log"

echo "🚀 [1/2] Syncing code to INF ($INF_IP)..."
# 同步代码 (含 scripts/launch_dual_track.py 和 config/trading_config.yaml)
rsync -avz --delete \
    --exclude 'venv' \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude 'logs/*' \
    --exclude 'VERIFY_LOG.log' \
    --exclude 'data/redis/*' \
    /opt/mt5-crs/ root@$INF_IP:/opt/mt5-crs/

echo "🔄 [2/2] Restarting service on INF..."
ssh root@$INF_IP "bash -s" << 'REMOTE_SCRIPT'
    # 停止旧进程
    pkill -f 'src.main.runner' || true
    pkill -f 'scripts/launch_dual_track.py' || true
    
    # 启动新进程
    cd /opt/mt5-crs/
    source venv/bin/activate
    # 使用专门的启动器
    nohup python3 scripts/launch_dual_track.py > logs/execution.log 2>&1 &
    
    sleep 2
    # 检查存活
    if ps aux | grep 'launch_dual_track.py' | grep -v grep; then
        echo "✅ Service restarted successfully."
    else
        echo "❌ Service failed to start. Check logs."
        exit 1
    fi
REMOTE_SCRIPT

echo "📄 Last 10 lines of INF logs:"
ssh root@$INF_IP "tail -n 10 /opt/mt5-crs/logs/execution.log"
