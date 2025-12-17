#!/bin/bash

# 简化的OSS备份测试脚本

echo "=== OSS备份测试开始 ==="

# 测试路径计算
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "SCRIPT_DIR: $SCRIPT_DIR"

# 从脚本目录向上查找项目根目录
find_project_root() {
    local current="$SCRIPT_DIR"
    while [ "$current" != "/" ]; do
        if [ -d "$current/.git" ] && [ -d "$current/.secrets" ]; then
            echo "$current"
            return 0
        fi
        current="$(dirname "$current")"
    done
    echo "$SCRIPT_DIR"  # fallback
}

PROJECT_ROOT="$(find_project_root)"
echo "PROJECT_ROOT: $PROJECT_ROOT"

# 检查关键文件
echo "检查OSS角色ARN文件..."
if [ -f "$PROJECT_ROOT/.secrets/oss_role_arn" ]; then
    echo "✓ OSS角色ARN文件存在"
    cat "$PROJECT_ROOT/.secrets/oss_role_arn"
else
    echo "✗ OSS角色ARN文件不存在"
fi

echo "检查钉钉配置文件..."
if [ -f "$PROJECT_ROOT/configs/grafana/provisioning/contact-points/dingtalk.yml" ]; then
    echo "✓ 钉钉配置文件存在"
else
    echo "✗ 钉钉配置文件不存在"
fi

echo "检查备份脚本..."
if [ -f "$SCRIPT_DIR/oss_backup.sh" ]; then
    echo "✓ 备份脚本存在"
    if bash -n "$SCRIPT_DIR/oss_backup.sh"; then
        echo "✓ 备份脚本语法正确"
    else
        echo "✗ 备份脚本语法错误"
    fi
else
    echo "✗ 备份脚本不存在"
fi

echo "检查数据目录..."
if [ -d "$PROJECT_ROOT/data/mt5" ]; then
    echo "✓ 数据目录存在"
    datasets_count=$(find "$PROJECT_ROOT/data/mt5/datasets" -name "*.csv" 2>/dev/null | wc -l)
    factors_count=$(find "$PROJECT_ROOT/data/mt5/factors" -name "*.csv" 2>/dev/null | wc -l)
    echo "数据集文件: $datasets_count 个"
    echo "因子文件: $factors_count 个"
else
    echo "✗ 数据目录不存在"
fi

echo "=== OSS备份测试完成 ==="
