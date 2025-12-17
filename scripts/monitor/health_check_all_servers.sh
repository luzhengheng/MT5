#!/bin/bash
# 全服务器健康检查脚本
# 版本：v1.0 (2025-12-16)
# 目标：99.9%可用性监控，自动化健康检查

set -e

cd /root/MT5-CRS

echo "🏥 全服务器健康检查开始 - $(date)"
echo "目标可用性：99.9%"

# 服务器列表和配置
declare -A servers=(
    ["47.84.1.161"]="hub"
    ["8.138.100.136"]="training"
    ["47.84.111.158"]="inference"
)

total_checks=0
passed_checks=0
failed_checks=()

# 检查函数
check_service() {
    local ip=$1
    local service=$2
    local check_cmd=$3
    local expected_output=$4

    total_checks=$((total_checks + 1))

    if ssh -o ConnectTimeout=5 -o BatchMode=yes "root@$ip" "$check_cmd" 2>/dev/null | grep -q "$expected_output"; then
        echo "  ✅ $service: 正常"
        passed_checks=$((passed_checks + 1))
        return 0
    else
        echo "  ❌ $service: 异常"
        failed_checks+=("$ip:$service")
        return 1
    fi
}

# 主检查循环
for ip in "${!servers[@]}"; do
    role="${servers[$ip]}"
    echo ""
    echo "🔍 检查 $role 服务器 ($ip):"

    # 1. 网络连接检查
    if ping -c 2 -W 3 "$ip" > /dev/null 2>&1; then
        echo "  ✅ 网络连接: 正常"
        network_ok=true
    else
        echo "  ❌ 网络连接: 失败"
        failed_checks+=("$ip:网络连接")
        continue
    fi

    # 2. SSH连接检查
    if ssh -o ConnectTimeout=5 -o BatchMode=yes "root@$ip" "echo 'SSH测试'" > /dev/null 2>&1; then
        echo "  ✅ SSH连接: 正常"
    else
        echo "  ❌ SSH连接: 失败"
        failed_checks+=("$ip:SSH连接")
        continue
    fi

    # 3. 根据服务器角色进行特定检查
    case $role in
        "hub")
            # 中枢服务器检查
            check_service "$ip" "GitHub Runner" "systemctl is-active actions-runner" "active"
            check_service "$ip" "Grafana" "docker ps" "grafana"
            check_service "$ip" "Prometheus" "docker ps" "prometheus"
            check_service "$ip" "Node Exporter" "docker ps" "node-exporter"

            # 系统资源检查
            cpu_usage=$(ssh "root@$ip" "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\([0-9.]*\)%* id.*/\1/' | awk '{print 100 - \$1}'" 2>/dev/null || echo "0")
            mem_usage=$(ssh "root@$ip" "free | grep Mem | awk '{printf \"%.1f\", \$3/\$2 * 100.0}'" 2>/dev/null || echo "0")
            disk_usage=$(ssh "root@$ip" "df / | tail -1 | awk '{print \$5}' | sed 's/%//'" 2>/dev/null || echo "0")

            echo "  📊 系统资源:"
            echo "    CPU: ${cpu_usage}%"
            echo "    内存: ${mem_usage}%"
            echo "    磁盘: ${disk_usage}%"

            # 资源阈值检查
            if (( $(echo "$cpu_usage > 80" | bc -l 2>/dev/null || echo "0") )); then
                echo "  ⚠️ CPU使用率过高"
                failed_checks+=("$ip:高CPU使用率")
            fi
            if (( $(echo "$mem_usage > 85" | bc -l 2>/dev/null || echo "0") )); then
                echo "  ⚠️ 内存使用率过高"
                failed_checks+=("$ip:高内存使用率")
            fi
            if (( disk_usage > 90 )); then
                echo "  ⚠️ 磁盘使用率过高"
                failed_checks+=("$ip:高磁盘使用率")
            fi
            ;;

        "training")
            # 训练服务器检查
            check_service "$ip" "GPU驱动" "nvidia-smi" "NVIDIA"

            # GPU内存检查
            gpu_mem=$(ssh "root@$ip" "nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null | head -1" || echo "0,0")
            IFS=',' read -r used total <<< "$gpu_mem"
            if [ "$total" != "0" ]; then
                gpu_usage=$(echo "scale=1; $used / $total * 100" | bc -l 2>/dev/null || echo "0")
                echo "  🎮 GPU内存: ${gpu_usage}% ($used/$total MB)"
            fi

            # 检查训练相关服务
            check_service "$ip" "Python环境" "python --version" "Python"
            check_service "$ip" "PyTorch" "python -c 'import torch; print(torch.__version__)'" "[0-9]"
            ;;

        "inference")
            # 推理服务器检查
            # 检查推理服务健康状态
            health_status=$(ssh "root@$ip" "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health 2>/dev/null" || echo "000")
            if [ "$health_status" = "200" ]; then
                echo "  ✅ 推理服务: 正常 (HTTP 200)"
                passed_checks=$((passed_checks + 1))
            else
                echo "  ❌ 推理服务: 异常 (HTTP $health_status)"
                failed_checks+=("$ip:推理服务")
            fi
            total_checks=$((total_checks + 1))

            # 检查ONNX Runtime
            check_service "$ip" "ONNX Runtime" "python -c 'import onnxruntime'" "success"

            # 检查响应时间
            response_time=$(ssh "root@$ip" "time -p curl -s http://localhost:8000/health 2>&1 | grep real | awk '{print \$2}'" 2>/dev/null || echo "0")
            response_ms=$(echo "$response_time * 1000" | bc -l 2>/dev/null | xargs printf "%.0f" 2>/dev/null || echo "0")
            echo "  ⚡ 响应时间: ${response_ms}ms"

            if (( response_ms > 50 )); then
                echo "  ⚠️ 响应时间超过50ms阈值"
                failed_checks+=("$ip:响应时间过慢")
            fi
            ;;
    esac
done

# 生成检查报告
echo ""
echo "📊 健康检查报告汇总"
echo "========================"
echo "总检查项目: $total_checks"
echo "通过项目: $passed_checks"
echo "失败项目: ${#failed_checks[@]}"

availability=$(echo "scale=3; $passed_checks / $total_checks * 100" | bc -l 2>/dev/null || echo "0")
echo "可用性: ${availability}%"

if [ ${#failed_checks[@]} -eq 0 ]; then
    echo "🎉 所有检查通过！系统运行正常。"
else
    echo ""
    echo "❌ 发现异常项目："
    for failure in "${failed_checks[@]}"; do
        echo "  - $failure"
    done
    echo ""
    echo "🔧 建议采取措施："
    echo "  1. 检查网络连接和SSH配置"
    echo "  2. 重启失败的服务"
    echo "  3. 检查系统资源使用情况"
    echo "  4. 查看详细日志以获取更多信息"
fi

# 检查是否达到99.9%可用性目标
target_availability=99.9
if (( $(echo "$availability >= $target_availability" | bc -l 2>/dev/null || echo "0") )); then
    echo "✅ 达到可用性目标 (99.9%)"
    exit_code=0
else
    echo "⚠️ 未达到可用性目标 (99.9%)"
    exit_code=1
fi

echo ""
echo "🏁 健康检查完成 - $(date)"
exit $exit_code
