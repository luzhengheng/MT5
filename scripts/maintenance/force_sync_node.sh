#!/bin/bash
#
# Force sync node with HUB (clean slate approach)
# Usage: ./scripts/maintenance/force_sync_node.sh <inf|gtw|gpu>
#

set -e

NODE=$1
SSH_OPTIONS="-o ConnectTimeout=10 -o StrictHostKeyChecking=no"

# Node configurations
case "$NODE" in
    inf)
        SSH_USER="root"
        SSH_HOST="172.19.141.250"
        REPO_PATH="/opt/mt5-crs"
        ;;
    gtw)
        SSH_USER="Administrator"
        SSH_HOST="172.19.141.255"
        REPO_PATH="C:/mt5-crs"
        ;;
    gpu)
        SSH_USER="root"
        SSH_HOST="www.guangzhoupeak.com"
        REPO_PATH="/opt/mt5-crs"
        ;;
    *)
        echo "Usage: $0 <inf|gtw|gpu>"
        exit 1
        ;;
esac

echo "========================================="
echo "强制同步 $NODE 节点"
echo "========================================="
echo "用户: $SSH_USER"
echo "主机: $SSH_HOST"
echo "路径: $REPO_PATH"
echo ""

# Get HUB hash
HUB_HASH=$(git rev-parse HEAD)
echo "HUB 当前 Hash: $HUB_HASH"
echo ""

# Execute sync on remote node
echo "开始同步..."
ssh $SSH_OPTIONS $SSH_USER@$SSH_HOST bash << 'ENDSSH'
set -e
NODE_NAME="$1"
REPO_PATH="$2"
TARGET_HASH="$3"

echo "=== [$NODE_NAME] 备份现有配置 ==="
if [ -f "$REPO_PATH/.env" ]; then
    cp "$REPO_PATH/.env" "$REPO_PATH/.env.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
fi

echo "=== [$NODE_NAME] 清理旧仓库 ==="
cd "$REPO_PATH" 2>/dev/null || true
rm -rf .git 2>/dev/null || true

echo "=== [$NODE_NAME] 初始化 Git 仓库 ==="
git init
git remote add origin https://github.com/luzhengheng/MT5.git

echo "=== [$NODE_NAME] 拉取最新代码 ==="
git fetch origin main

echo "=== [$NODE_NAME] 强制重置到 main ==="
git reset --hard origin/main

echo "=== [$NODE_NAME] 清理未跟踪文件 ==="
git clean -fd -X

echo "=== [$NODE_NAME] 验证 Hash ==="
LOCAL_HASH=$(git rev-parse HEAD)
echo "本地 Hash: $LOCAL_HASH"

if [ "$LOCAL_HASH" = "$TARGET_HASH" ]; then
    echo "✅ [$NODE_NAME] 同步成功！"
else
    echo "⚠️  [$NODE_NAME] Hash 不匹配"
    echo "   期望: $TARGET_HASH"
    echo "   实际: $LOCAL_HASH"
fi

echo "=== [$NODE_NAME] 恢复配置文件 ==="
if [ -f .env.backup.* ]; then
    latest_backup=$(ls -t .env.backup.* 2>/dev/null | head -1)
    if [ -n "$latest_backup" ]; then
        cp "$latest_backup" .env
        echo "✅ 已恢复 .env 配置"
    fi
fi

ENDSSH

echo ""
echo "========================================="
echo "✅ $NODE 同步完成"
echo "========================================="
