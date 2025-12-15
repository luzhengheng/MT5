#!/bin/bash

# MT5 Hub 钉钉告警配置脚本
# 配置钉钉 webhook 和 Grafana 告警规则

set -e

echo "🚀 配置钉钉告警系统..."

# 检查参数
if [ $# -ne 1 ]; then
    echo "用法: $0 <钉钉 Webhook URL>"
    echo "例如: $0 https://oapi.dingtalk.com/robot/send?access_token=YOUR_ACCESS_TOKEN"
    echo ""
    echo "如何获取钉钉 Webhook URL:"
    echo "1. 打开钉钉，创建或选择群聊"
    echo "2. 添加自定义机器人"
    echo "3. 设置机器人名称和安全选项"
    echo "4. 复制生成的 webhook URL"
    exit 1
fi

WEBHOOK_URL=$1

# 备份原始配置
cp configs/grafana/provisioning/notifiers/dingtalk.yml configs/grafana/provisioning/notifiers/dingtalk.yml.backup

# 更新钉钉配置
sed -i "s|https://oapi.dingtalk.com/robot/send?access_token=YOUR_DINGTALK_ACCESS_TOKEN|$WEBHOOK_URL|" configs/grafana/provisioning/notifiers/dingtalk.yml

echo "✅ 钉钉 webhook URL 已更新"

# 重启 Grafana 以应用配置
echo "🔄 重启 Grafana 以应用新配置..."
docker restart grafana

# 等待 Grafana 重启
sleep 10

echo "✅ Grafana 已重启"

# 创建告警规则文件
cat > configs/grafana/provisioning/alerting/rules.yml << 'EOF'
apiVersion: 1

groups:
  - name: mt5_system_alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is {{ $value | printf "%.2f" }}% on {{ $labels.instance }}"

      - alert: HighMemoryUsage
        expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is {{ $value | printf "%.2f" }}% on {{ $labels.instance }}"

      - alert: LowDiskSpace
        expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100 > 90
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space"
          description: "Disk usage is {{ $value | printf "%.2f" }}% on {{ $labels.mountpoint }}"

      - alert: ServiceDown
        expr: up{job="grafana"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Grafana service is down"
          description: "Grafana service has been down for more than 1 minute"

      - alert: MT5ServiceDown
        expr: up{job="mt5-service"} == 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "MT5 service is down"
          description: "MT5 service has been down for more than 5 minutes"
EOF

echo "✅ 告警规则已创建"

# 测试钉钉告警
echo "🧪 测试钉钉告警..."

# 创建测试告警消息（使用markdown格式）
TEST_MESSAGE='{
  "msgtype": "markdown",
  "markdown": {
    "title": "MT5 Hub 监控告警测试",
    "text": "# 🧪 MT5 Hub 监控告警测试\n\n✅ 钉钉 webhook 配置成功！\n\n⏰ 测试时间: '$(date)'\n\n📊 系统状态: 正常\n\n此消息确认告警系统已正确配置。\n\n---\n\n**测试状态**: ✅ 通过\n\n**配置时间**: '$(date)'"
  },
  "at": {
    "isAtAll": false
  }
}'

# 发送测试消息
curl -s -X POST -H 'Content-type: application/json' --data "$TEST_MESSAGE" "$WEBHOOK_URL" > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ 测试消息已发送到钉钉群"
    echo "📱 请检查您的钉钉群是否收到测试消息"
else
    echo "❌ 发送测试消息失败"
    exit 1
fi

echo ""
echo "🎉 钉钉告警配置完成！"
echo ""
echo "📋 配置摘要:"
echo "- Webhook URL: 已配置"
echo "- 联系点: dingtalk-mt5-alerts"
echo "- 告警规则: 5个系统监控规则"
echo "- 测试消息: 已发送"
echo ""
echo "📊 告警规则包括:"
echo "- 高CPU使用率 (>80%)"
echo "- 高内存使用率 (>85%)"
echo "- 低磁盘空间 (<10%)"
echo "- Grafana服务宕机"
echo "- MT5服务宕机"