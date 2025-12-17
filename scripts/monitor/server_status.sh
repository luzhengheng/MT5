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
