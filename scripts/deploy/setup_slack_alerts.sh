#!/bin/bash

# MT5 Hub Slack 告警配置脚本
# 配置 Slack webhook 和 Grafana 告警规则

set -e

echo "🚀 配置 Slack 告警系统..."

# 检查参数
if [ $# -ne 1 ]; then
    echo "用法: $0 <Slack Webhook URL>"
    echo "例如: $0 https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    echo ""
    echo "如何获取 Slack Webhook URL:"
    echo "1. 访问 https://api.slack.com/apps"
    echo "2. 创建新应用或选择现有应用"
    echo "3. 启用 Incoming Webhooks"
    echo "4. 添加 webhook 到工作区"
    echo "5. 复制 webhook URL"
    exit 1
fi

WEBHOOK_URL=$1

# 备份原始配置
cp configs/grafana/provisioning/notifiers/slack.yml configs/grafana/provisioning/notifiers/slack.yml.backup

# 更新 Slack 配置
sed -i "s|https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK|$WEBHOOK_URL|" configs/grafana/provisioning/notifiers/slack.yml

echo "✅ Slack webhook URL 已更新"

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

# 测试 Slack 告警
echo "🧪 测试 Slack 告警..."

# 创建测试告警消息
TEST_MESSAGE='{
  "channel": "#mt5-alerts",
  "username": "MT5 Hub Alert",
  "icon_emoji": ":chart_with_upwards_trend:",
  "text": "🧪 *MT5 Hub 监控告警测试*\n\n✅ Slack webhook 配置成功！\n⏰ 测试时间: '$(date)'\n📊 系统状态: 正常\n\n此消息确认告警系统已正确配置。",
  "attachments": [
    {
      "color": "good",
      "fields": [
        {
          "title": "测试状态",
          "value": "✅ 通过",
          "short": true
        },
        {
          "title": "配置时间",
          "value": "'$(date)'",
          "short": true
        }
      ]
    }
  ]
}'

# 发送测试消息
curl -s -X POST -H 'Content-type: application/json' --data "$TEST_MESSAGE" "$WEBHOOK_URL" > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ 测试消息已发送到 Slack"
    echo "📱 请检查您的 Slack 频道是否收到测试消息"
else
    echo "❌ 发送测试消息失败"
    exit 1
fi

echo ""
echo "🎉 Slack 告警配置完成！"
echo ""
echo "📋 配置摘要:"
echo "- Webhook URL: 已配置"
echo "- 联系点: slack-mt5-alerts"
echo "- 告警规则: 5个系统监控规则"
echo "- 测试消息: 已发送"
echo ""
echo "📊 告警规则包括:"
echo "- 高CPU使用率 (>80%)"
echo "- 高内存使用率 (>85%)"
echo "- 低磁盘空间 (<10%)"
echo "- Grafana服务宕机"
echo "- MT5服务宕机"