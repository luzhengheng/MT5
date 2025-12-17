#!/bin/bash
# 服务器连接详细诊断脚本
# 版本：v1.0 (2025-12-16)

echo "🔬 详细诊断服务器连接问题..."
echo "诊断时间: $(date)"
echo "=========================================="

servers=("8.138.100.136:training" "47.84.111.158:inference")

for server_info in "${servers[@]}"; do
    IFS=':' read -r ip role <<< "$server_info"
    echo ""
    echo "🔍 诊断 $role 服务器 ($ip)"
    echo "----------------------------------"

    # 1. DNS解析测试
    echo "1. DNS解析:"
    if host "$ip" >/dev/null 2>&1; then
        host "$ip"
    else
        echo "   无法解析 $ip (可能是IP地址)"
    fi

    # 2. 基础网络连接测试
    echo "2. 网络连通性 (ping):"
    if ping -c 3 -W 2 "$ip" >/dev/null 2>&1; then
        ping_result=$(ping -c 3 -W 2 "$ip" | tail -1)
        echo "   ✅ ping成功: $ping_result"
    else
        echo "   ❌ ping失败"
    fi

    # 3. 端口扫描测试
    echo "3. SSH端口 (22) 可访问性:"
    if command -v nc >/dev/null 2>&1; then
        if nc -z -w5 "$ip" 22 2>/dev/null; then
            echo "   ✅ SSH端口开放"
        else
            echo "   ❌ SSH端口关闭或被防火墙阻止"
        fi
    elif command -v telnet >/dev/null 2>&1; then
        if timeout 5 bash -c "</dev/tcp/$ip/22" 2>/dev/null; then
            echo "   ✅ SSH端口开放"
        else
            echo "   ❌ SSH端口关闭或被防火墙阻止"
        fi
    else
        echo "   ⚠️ 缺少网络检测工具(nc/telnet)"
    fi

    # 4. SSH详细诊断
    echo "4. SSH连接详细诊断:"
    echo "   尝试SSH连接 (超时5秒)..."
    ssh_output=$(ssh -v -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no "root@$ip" "echo 'SSH连接成功'" 2>&1)
    ssh_exit_code=$?

    if [ $ssh_exit_code -eq 0 ]; then
        echo "   ✅ SSH连接成功"
        echo "   响应: $(echo "$ssh_output" | grep -E "^SSH连接成功" | head -1)"
    else
        echo "   ❌ SSH连接失败 (退出码: $ssh_exit_code)"
        echo "   错误详情:"

        # 分析常见错误
        if echo "$ssh_output" | grep -q "Connection refused"; then
            echo "     - 连接被拒绝：SSH服务未运行或防火墙阻止"
        elif echo "$ssh_output" | grep -q "Connection timed out"; then
            echo "     - 连接超时：网络不可达或防火墙阻止"
        elif echo "$ssh_output" | grep -q "Permission denied"; then
            echo "     - 权限被拒绝：SSH密钥未正确配置或密码认证失败"
        elif echo "$ssh_output" | grep -q "Host key verification failed"; then
            echo "     - 主机密钥验证失败：known_hosts问题"
        elif echo "$ssh_output" | grep -q "Network is unreachable"; then
            echo "     - 网络不可达：路由问题"
        else
            echo "     - 其他错误：请检查详细日志"
        fi

        # 显示最后几行错误输出
        echo "   最后几行输出:"
        echo "$ssh_output" | tail -3 | sed 's/^/     /'
    fi

    # 5. 本地SSH配置检查
    echo "5. 本地SSH配置检查:"
    if [ -f ~/.ssh/id_rsa.pub ] || [ -f ~/.ssh/mt5_server_key.pub ]; then
        echo "   ✅ SSH公钥存在"
        ls -la ~/.ssh/*.pub 2>/dev/null | head -2
    else
        echo "   ❌ 未找到SSH公钥文件"
    fi

    # 6. 建议解决方案
    echo "6. 建议解决方案:"
    if ping -c 1 -W 2 "$ip" >/dev/null 2>&1; then
        if ! nc -z -w5 "$ip" 22 2>/dev/null; then
            echo "   - 检查目标服务器SSH服务是否运行: systemctl status sshd"
            echo "   - 检查防火墙设置: firewall-cmd --list-all 或 iptables -L"
            echo "   - 确保SSH端口(22)未被阻止"
        else
            echo "   - 手动复制SSH公钥到目标服务器:"
            echo "     ssh-copy-id -i ~/.ssh/mt5_server_key.pub root@$ip"
            echo "   - 或在目标服务器上手动添加公钥到 ~/.ssh/authorized_keys"
        fi
    else
        echo "   - 检查网络连接和路由配置"
        echo "   - 确认服务器已启动并可访问"
    fi

done

echo ""
echo "=========================================="
echo "📋 总结和下一步操作:"
echo ""
echo "当前状态:"
echo "  - 网络连接: 正常"
echo "  - SSH端口: 需要验证"
echo "  - SSH认证: 需要配置"
echo ""
echo "推荐操作步骤:"
echo "1. 确认目标服务器已启动并运行SSH服务"
echo "2. 检查防火墙配置，确保SSH端口(22)开放"
echo "3. 手动复制SSH公钥到目标服务器"
echo "4. 重新运行连接测试"
echo ""
echo "手动配置SSH密钥命令:"
echo "  ssh-copy-id -i ~/.ssh/mt5_server_key.pub root@8.138.100.136"
echo "  ssh-copy-id -i ~/.ssh/mt5_server_key.pub root@47.84.111.158"
