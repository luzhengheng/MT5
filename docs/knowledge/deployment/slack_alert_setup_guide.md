# Slack 告警配置指南

## 概述

本指南介绍如何配置 Slack 告警系统，实现 MT5 Hub 监控系统的自动告警通知。

## 前置条件

- 已部署 Grafana 监控系统
- 拥有 Slack 工作区管理员权限
- 已部署 Prometheus/Node Exporter

## 配置步骤

### 1. 创建 Slack 应用

1. 访问 [Slack API](https://api.slack.com/apps)
2. 点击 "Create New App" → "From scratch"
3. 输入应用名称: `MT5 Hub Alerts`
4. 选择您的 Slack 工作区

### 2. 启用 Webhooks

1. 在应用设置页面，点击 "Incoming Webhooks"
2. 切换 "Activate Incoming Webhooks" 为 "On"
3. 点击 "Add New Webhook to Workspace"
4. 选择告警消息要发送的频道（建议创建 `#mt5-alerts` 频道）
5. 复制生成的 Webhook URL

### 3. 运行配置脚本

```bash
# 使用复制的 Webhook URL
./scripts/deploy/setup_slack_alerts.sh "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
```

## 告警规则说明

配置完成后，系统会监控以下指标：

### 系统性能告警

| 告警名称 | 条件 | 级别 | 说明 |
|---------|------|------|------|
| HighCPUUsage | CPU > 80% (持续5分钟) | 警告 | 高CPU使用率 |
| HighMemoryUsage | 内存 > 85% (持续5分钟) | 警告 | 高内存使用率 |
| LowDiskSpace | 磁盘 < 10% (持续10分钟) | 严重 | 磁盘空间不足 |

### 服务可用性告警

| 告警名称 | 条件 | 级别 | 说明 |
|---------|------|------|------|
| ServiceDown | Grafana 服务宕机 (持续1分钟) | 严重 | Grafana服务不可用 |
| MT5ServiceDown | MT5 服务宕机 (持续5分钟) | 警告 | MT5服务不可用 |

## 告警消息格式

Slack 告警消息包含以下信息：

```
🔔 [FIRING:1] mt5_system_alerts HighCPUUsage

高CPU使用率检测到
CPU usage is 85.32% on localhost

Labels:
alertname=HighCPUUsage
instance=localhost
job=node
severity=warning

Annotations:
description=CPU usage is 85.32% on localhost
summary=High CPU usage detected
```

## 故障排除

### 告警不触发

1. 检查 Prometheus 目标状态：
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

2. 验证 Grafana 告警规则：
   - 访问 http://47.84.1.161:3000
   - 进入 Alerting → Alert rules

### Slack 消息不发送

1. 检查 webhook URL 是否正确
2. 验证 Slack 应用权限
3. 查看 Grafana 日志：
   ```bash
   docker logs grafana
   ```

## 自定义配置

### 添加新告警规则

编辑 `configs/grafana/provisioning/alerting/rules.yml`：

```yaml
- alert: CustomAlert
  expr: your_promql_expression
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Custom alert summary"
    description: "Custom alert description"
```

### 修改告警阈值

在 rules.yml 中调整告警条件：

```yaml
# 修改 CPU 告警阈值从 80% 到 90%
expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
```

## 维护指南

### 定期检查

- 每周检查告警规则是否正常工作
- 每月验证 webhook URL 有效性
- 定期审查告警阈值是否合理

### 日志监控

```bash
# 查看 Grafana 告警日志
docker logs grafana 2>&1 | grep -i alert

# 查看 Prometheus 告警状态
curl http://localhost:9090/api/v1/alerts
```

## 安全注意事项

- Webhook URL 包含敏感信息，请妥善保管
- 定期轮换 webhook URL
- 限制 Slack 频道的访问权限
- 监控告警消息的使用情况

## 版本信息

- Slack API: Latest
- Grafana: 12.3.0
- Prometheus: 2.53.2
- 配置版本: v1.0 (2025-12-15)