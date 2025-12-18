#!/bin/bash
# 防火墙端口精细配置脚本
# 为监控和告警系统开放必要端口

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}防火墙端口配置脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检测防火墙类型
detect_firewall() {
    if systemctl is-active --quiet firewalld 2>/dev/null; then
        echo "firewalld"
    elif systemctl is-active --quiet iptables 2>/dev/null; then
        echo "iptables"
    elif command -v ufw &>/dev/null && ufw status 2>/dev/null | grep -q "Status: active"; then
        echo "ufw"
    else
        echo "none"
    fi
}

FIREWALL_TYPE=$(detect_firewall)

echo -e "${YELLOW}检测到的防火墙类型: ${FIREWALL_TYPE}${NC}"
echo ""

if [ "$FIREWALL_TYPE" == "none" ]; then
    echo -e "${YELLOW}⚠️  未检测到活动的防火墙${NC}"
    echo "建议安装并启用防火墙以增强安全性"
    exit 0
fi

# 定义需要开放的端口 - firewalld 方式
echo -e "${YELLOW}配置 firewalld...${NC}"

# 确保 firewalld 运行
if [ "$FIREWALL_TYPE" == "firewalld" ]; then
    systemctl restart firewalld 2>/dev/null || true
    sleep 2

    echo "开放监控相关端口..."

    # Prometheus 9090
    firewall-cmd --permanent --add-rich-rule="rule family=ipv4 source address=127.0.0.1 port port=9090 protocol=tcp accept" 2>/dev/null || true
    firewall-cmd --add-rich-rule="rule family=ipv4 source address=127.0.0.1 port port=9090 protocol=tcp accept" 2>/dev/null || true
    echo "✅ Prometheus 9090 (localhost)"

    # Alertmanager 9093
    firewall-cmd --permanent --add-rich-rule="rule family=ipv4 source address=127.0.0.1 port port=9093 protocol=tcp accept" 2>/dev/null || true
    firewall-cmd --add-rich-rule="rule family=ipv4 source address=127.0.0.1 port port=9093 protocol=tcp accept" 2>/dev/null || true
    echo "✅ Alertmanager 9093 (localhost)"

    # Node Exporter 9100
    firewall-cmd --permanent --add-rich-rule="rule family=ipv4 source address=127.0.0.1 port port=9100 protocol=tcp accept" 2>/dev/null || true
    firewall-cmd --add-rich-rule="rule family=ipv4 source address=127.0.0.1 port port=9100 protocol=tcp accept" 2>/dev/null || true
    echo "✅ Node Exporter 9100 (localhost)"

    # Pushgateway 9091
    firewall-cmd --permanent --add-rich-rule="rule family=ipv4 source address=127.0.0.1 port port=9091 protocol=tcp accept" 2>/dev/null || true
    firewall-cmd --add-rich-rule="rule family=ipv4 source address=127.0.0.1 port port=9091 protocol=tcp accept" 2>/dev/null || true
    echo "✅ Pushgateway 9091 (localhost)"

    # Grafana 3000
    firewall-cmd --permanent --add-port=3000/tcp 2>/dev/null || true
    firewall-cmd --add-port=3000/tcp 2>/dev/null || true
    echo "✅ Grafana 3000 (public)"

    # Webhook 5001 - 仅内网
    for ip in 127.0.0.1 47.84.1.161 47.84.111.158 8.138.100.136 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 100.64.0.0/10; do
        firewall-cmd --permanent --add-rich-rule="rule family=ipv4 source address=$ip port port=5001 protocol=tcp accept" 2>/dev/null || true
        firewall-cmd --add-rich-rule="rule family=ipv4 source address=$ip port port=5001 protocol=tcp accept" 2>/dev/null || true
    done
    echo "✅ Webhook 5001 (内网+localhost)"

    # SSH 22
    firewall-cmd --permanent --add-service=ssh 2>/dev/null || true
    firewall-cmd --add-service=ssh 2>/dev/null || true
    echo "✅ SSH 22 (public)"

    # HTTP/HTTPS
    firewall-cmd --permanent --add-service=http 2>/dev/null || true
    firewall-cmd --add-service=http 2>/dev/null || true
    firewall-cmd --permanent --add-service=https 2>/dev/null || true
    firewall-cmd --add-service=https 2>/dev/null || true
    echo "✅ HTTP 80 / HTTPS 443 (public)"

    # 重载防火墙
    echo ""
    echo "重载防火墙..."
    firewall-cmd --reload 2>/dev/null || true

    echo ""
    echo "当前防火墙配置:"
    firewall-cmd --list-all 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}防火墙配置完成!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
