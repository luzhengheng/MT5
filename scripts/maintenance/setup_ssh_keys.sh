#!/bin/bash
#
# SSH Key Distribution Script (Password-based)
#
# This script helps distribute SSH public keys to all nodes using password authentication.
# Run this on HUB (sg-nexus-hub-01) once to enable passwordless SSH for future operations.
#

set -e

echo "========================================"
echo "SSH 密钥分发向导"
echo "========================================"
echo ""

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    echo "❌ 未找到 SSH 公钥 ~/.ssh/id_rsa.pub"
    echo "正在生成新的 SSH 密钥对..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
    echo "✅ SSH 密钥已生成"
fi

echo ""
echo "📧 您的 SSH 公钥内容:"
echo "----------------------------------------"
cat ~/.ssh/id_rsa.pub
echo "----------------------------------------"
echo ""

# Function to copy key to node
copy_key_to_node() {
    local node_name=$1
    local user=$2
    local host=$3
    local port=${4:-22}

    echo ""
    echo "🔧 配置 $node_name 节点..."
    echo "   用户: $user"
    echo "   主机: $host"
    echo "   端口: $port"
    echo ""
    echo "⚠️  当提示输入密码时，请输入该节点的 SSH 密码"
    echo ""

    # Use ssh-copy-id with password
    ssh-copy-id -i ~/.ssh/id_rsa.pub -p $port $user@$host

    if [ $? -eq 0 ]; then
        echo "✅ $node_name 密钥配置成功"
    else
        echo "❌ $node_name 密钥配置失败"
        return 1
    fi
}

# Main execution
echo "开始配置各节点..."
echo ""

# INF 节点 (内网 IP)
echo "=========================================="
echo "1️⃣  配置 INF 节点 (推理服务器)"
echo "=========================================="
copy_key_to_node "INF" "root" "172.19.141.250" "22"

# GTW 节点 (Windows, 内网 IP)
echo ""
echo "=========================================="
echo "2️⃣  配置 GTW 节点 (MT5 网关)"
echo "=========================================="
echo "⚠️  Windows 节点需要手动配置"
echo ""
echo "请按照以下步骤操作:"
echo "1. 手动 SSH 登录: ssh Administrator@172.19.141.255"
echo "2. 创建 .ssh 目录: mkdir -p C:/Users/Administrator/.ssh"
echo "3. 创建 authorized_keys: notepad C:/Users/Administrator/.ssh/authorized_keys"
echo "4. 将���下公钥内容粘贴到文件中并保存:"
echo "----------------------------------------"
cat ~/.ssh/id_rsa.pub
echo "--------------------------------========"
echo ""
read -p "按 Enter 键完成 GTW 配置后继续..."

# GPU 节点 (公网)
echo ""
echo "=========================================="
echo "3️⃣  配置 GPU 节点 (训练服务器)"
echo "=========================================="
copy_key_to_node "GPU" "root" "www.guangzhoupeak.com" "22"

# Verification
echo ""
echo "=========================================="
echo "🔍 验证 SSH 连接"
echo "=========================================="

echo ""
echo "测试 INF 节点..."
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no root@172.19.141.250 "echo '✅ INF 连接成功'" 2>/dev/null; then
    echo "✅ INF 节点验证通过"
else
    echo "❌ INF 节点验证失败"
fi

echo ""
echo "测试 GPU 节点..."
if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@www.guangzhoupeak.com "echo '✅ GPU 连接成功'" 2>/dev/null; then
    echo "✅ GPU 节点验证通过"
else
    echo "❌ GPU 节点验证失败"
fi

echo ""
echo "=========================================="
echo "✅ SSH 密钥配置完成！"
echo "=========================================="
echo ""
echo "下一步: 执行全网同步"
echo "  cd /opt/mt5-crs"
echo "  ./scripts/maintenance/sync_nodes.sh"
echo ""
