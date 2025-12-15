#!/bin/bash
# 跨服务器自动化部署脚本
# 版本：v1.0 (2025-12-16)
# 目的：建立中枢服务器与其他服务器的自动化协作框架

set -e

cd /root/MT5-CRS

echo "🚀 开始配置跨服务器自动化协作框架..."

# 检查服务器矩阵配置
if [ ! -f "configs/server_matrix.yml" ]; then
    echo "❌ 错误：未找到服务器矩阵配置文件"
    exit 1
fi

# 生成SSH密钥对
SSH_KEY_PATH="$HOME/.ssh/mt5_server_key"
echo "🔑 生成SSH密钥对..."
if [ ! -f "$SSH_KEY_PATH" ]; then
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N "" -C "mt5-server-automation-$(date +%Y%m%d)"
    echo "✅ SSH密钥对生成完成"
else
    echo "ℹ️ SSH密钥对已存在，跳过生成"
fi

# 配置服务器矩阵
declare -A servers=(
    ["training"]="8.138.100.136"
    ["inference"]="47.84.111.158"
)

# 创建known_hosts文件
touch "$HOME/.ssh/known_hosts"

# 部署公钥到各服务器
for server in "${!servers[@]}"; do
    ip="${servers[$server]}"
    echo "🔗 配置连接到 $server 服务器 ($ip)..."

    # 添加到known_hosts（避免交互式确认）
    ssh-keyscan -H "$ip" >> "$HOME/.ssh/known_hosts" 2>/dev/null || true

    # 复制公钥（需要手动确认或预先配置）
    echo "📤 尝试部署SSH公钥到 $server..."
    if ssh-copy-id -i "$SSH_KEY_PATH.pub" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "root@$ip" 2>/dev/null; then
        echo "✅ $server ($ip) SSH密钥部署成功"
    else
        echo "⚠️ $server ($ip) SSH密钥部署失败，可能需要手动配置"
        echo "手动配置命令："
        echo "  ssh-copy-id -i $SSH_KEY_PATH.pub root@$ip"
    fi
done

# 创建服务器间通信测试脚本
cat > scripts/monitor/test_server_connectivity.sh << 'EOF'
#!/bin/bash
# 测试服务器间连接性
# 版本：v1.0 (2025-12-16)

echo "🔍 测试跨服务器连接性..."

servers=("8.138.100.136" "47.84.111.158")
failed_servers=()

for ip in "${servers[@]}"; do
    echo ""
    echo "测试连接到 $ip..."

    # 测试基本网络连接
    if ping -c 2 -W 3 "$ip" > /dev/null 2>&1; then
        echo "✅ 网络连接: 正常"

        # 测试SSH连接
        if ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no "root@$ip" "echo 'SSH连接测试成功'" > /dev/null 2>&1; then
            echo "✅ SSH连接: 正常"

            # 测试基本命令执行
            server_info=$(ssh -o ConnectTimeout=5 "root@$ip" "uname -a" 2>/dev/null || echo "获取失败")
            echo "ℹ️ 服务器信息: $server_info"

        else
            echo "❌ SSH连接: 失败"
            failed_servers+=("$ip")
        fi
    else
        echo "❌ 网络连接: 失败"
        failed_servers+=("$ip")
    fi
done

echo ""
if [ ${#failed_servers[@]} -eq 0 ]; then
    echo "🎉 所有服务器连接测试通过！"
    exit 0
else
    echo "⚠️ 以下服务器连接失败："
    printf '  - %s\n' "${failed_servers[@]}"
    echo "请检查网络连接和SSH配置"
    exit 1
fi
EOF
chmod +x scripts/monitor/test_server_connectivity.sh

# 创建服务器状态监控脚本
cat > scripts/monitor/server_status.sh << 'EOF'
#!/bin/bash
# 服务器状态监控脚本
# 版本：v1.0 (2025-12-16)

echo "📊 服务器状态监控报告 - $(date)"

# 中枢服务器状态
echo ""
echo "🏠 中枢服务器 (47.84.1.161):"
echo "  服务状态:"
systemctl is-active --quiet actions-runner && echo "  ✅ GitHub Runner: 运行中" || echo "  ❌ GitHub Runner: 停止"
docker ps | grep -q grafana && echo "  ✅ Grafana: 运行中" || echo "  ❌ Grafana: 停止"
docker ps | grep -q prometheus && echo "  ✅ Prometheus: 运行中" || echo "  ❌ Prometheus: 停止"
docker ps | grep -q node-exporter && echo "  ✅ Node Exporter: 运行中" || echo "  ❌ Node Exporter: 停止"

echo "  系统资源:"
cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')
mem_usage=$(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')
disk_usage=$(df / | tail -1 | awk '{print $5}')

echo "  ✅ CPU使用率: $cpu_usage"
echo "  ✅ 内存使用率: $mem_usage"
echo "  ✅ 磁盘使用率: $disk_usage"

# 检查其他服务器（如果SSH连接正常）
echo ""
echo "🔗 检查其他服务器状态:"

servers=("8.138.100.136:training" "47.84.111.158:inference")

for server_info in "${servers[@]}"; do
    IFS=':' read -r ip role <<< "$server_info"
    echo ""
    echo "🖥️ $role 服务器 ($ip):"

    if ssh -o ConnectTimeout=5 -o BatchMode=yes "root@$ip" "echo '连接正常'" > /dev/null 2>&1; then
        echo "  ✅ 连接: 正常"

        # 获取基本系统信息
        uptime_info=$(ssh "root@$ip" "uptime -p" 2>/dev/null || echo "未知")
        echo "  ℹ️ 系统运行时间: $uptime_info"

        # 检查GPU状态（训练服务器）
        if [ "$role" = "training" ]; then
            gpu_info=$(ssh "root@$ip" "nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null | head -1" || echo "GPU不可用")
            echo "  🎮 GPU状态: $gpu_info"
        fi

        # 检查推理服务状态（推理服务器）
        if [ "$role" = "inference" ]; then
            service_status=$(ssh "root@$ip" "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health 2>/dev/null || echo '服务未运行'")
            if [ "$service_status" = "200" ]; then
                echo "  ✅ 推理服务: 运行正常"
            else
                echo "  ❌ 推理服务: 状态码 $service_status"
            fi
        fi

    else
        echo "  ❌ 连接: 失败"
    fi
done

echo ""
echo "📈 监控报告生成完成"
EOF
chmod +x scripts/monitor/server_status.sh

echo "✅ 跨服务器自动化协作框架配置完成"
echo ""
echo "🔧 可用脚本："
echo "  - scripts/monitor/test_server_connectivity.sh : 测试服务器连接"
echo "  - scripts/monitor/server_status.sh : 查看服务器状态"
echo ""
echo "📝 下一步："
echo "  1. 手动配置SSH密钥到其他服务器（如果自动部署失败）"
echo "  2. 运行连接测试：./scripts/monitor/test_server_connectivity.sh"
echo "  3. 查看状态报告：./scripts/monitor/server_status.sh"
