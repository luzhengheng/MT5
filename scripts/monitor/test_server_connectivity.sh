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
