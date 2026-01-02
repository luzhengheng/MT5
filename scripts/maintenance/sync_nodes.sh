#!/bin/bash
# TASK #017 - 全网节点文档同步脚本
# 将标准化归档同步至 INF/GTW/GPU 节点

set -e

# 配置
SOURCE_DIR="docs/archive/tasks/"
TARGETS=("inf" "gtw" "gpu")
EXCLUDE_TARGETS=()

# 节点配置（从基础设施档案读取）
declare -A NODE_HOSTS=(
    ["inf"]="root@www.crestive.net"
    ["gtw"]="Administrator@gtw.crestive.net"
    ["gpu"]="root@www.guangzhoupeak.com"
)

declare -A NODE_PATHS=(
    ["inf"]="/opt/mt5-crs/docs/archive/tasks/"
    ["gtw"]="/cygdrive/c/mt5-crs/docs/archive/tasks/"
    ["gpu"]="/opt/mt5-crs/docs/archive/tasks/"
)

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            TARGETS=("$2")
            shift 2
            ;;
        --exclude)
            EXCLUDE_TARGETS+=("$2")
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# 同步函数
sync_node() {
    local node=$1
    local host=${NODE_HOSTS[$node]}
    local path=${NODE_PATHS[$node]}

    echo "=========================================="
    echo "Syncing to: $node ($host)"
    echo "=========================================="

    # 检查节点是否在线
    if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$host" "echo 2>&1" &>/dev/null; then
        echo "⚠️  Node $node is offline or unreachable, skipping..."
        return 1
    fi

    # 执行同步
    rsync -avz --progress \
        --exclude=".git" \
        --exclude="*.pyc" \
        "$SOURCE_DIR" \
        "$host:$path"

    echo "✅ Sync to $node completed"
    echo ""
}

# 主逻辑
echo "🚀 MT5-CRS Fleet Documentation Sync"
echo "Source: $SOURCE_DIR"
echo ""

for node in "${TARGETS[@]}"; do
    # 检查是否在排除列表
    if [[ " ${EXCLUDE_TARGETS[@]} " =~ " ${node} " ]]; then
        echo "⏭️  Skipping $node (excluded)"
        continue
    fi

    sync_node "$node" || echo "❌ Failed to sync $node"
done

echo "=========================================="
echo "✅ Fleet sync completed"
echo "=========================================="
