# 钉钉告警配置指南

## 概述

本指南介绍如何配置钉钉告警系统，实现 MT5 Hub 监控系统的自动告警通知。

## 前置条件

- 已部署 Grafana 监控系统
- 拥有钉钉群管理员权限
- 已部署 Prometheus/Node Exporter

## 配置步骤

### 1. 创建钉钉群聊

1. 打开钉钉应用
2. 创建新群聊或选择现有群聊（建议创建专用告警群）
3. 设置群名为：`MT5 Hub 监控告警`

### 2. 添加自定义机器人

1. 在群聊中点击右上角"..." → "群设置"
2. 点击"智能群助手" → "添加机器人"
3. 选择"自定义机器人"
4. 输入机器人名称：`MT5 Hub Alert`
5. 选择机器人头像（建议选择监控/告警相关的图标）
6. 设置安全设置：
   - **必须选择"自定义关键词"**：设置关键词 `告警`、`监控`、`MT5`、`系统`
   - 不要选择"加签"方式（会增加配置复杂度）

### 3. 获取Webhook URL

1. 添加机器人后，系统会显示Webhook URL
2. 复制完整的Webhook URL（格式类似：`https://oapi.dingtalk.com/robot/send?access_token=XXXXXXXXXXXXXXXXXXXXXXX`）
3. **重要**：妥善保存此URL，包含敏感的access_token信息

### 4. 运行配置脚本

```bash
# 使用复制的 Webhook URL
./scripts/deploy/setup_dingtalk_alerts.sh "https://oapi.dingtalk.com/robot/send?access_token=YOUR_ACCESS_TOKEN"
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

钉钉告警消息包含以下信息：

```
🔔 [FIRING:1] mt5_system_alerts HighCPUUsage

**高CPU使用率检测到**
CPU usage is 85.32% on localhost

**Labels:**
- alertname: HighCPUUsage
- instance: localhost
- job: node
- severity: warning

**Annotations:**
- description: CPU usage is 85.32% on localhost
- summary: High CPU usage detected
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

### 钉钉消息不发送

1. 检查 webhook URL 是否正确
2. 验证机器人权限和关键词设置
3. 查看 Grafana 日志：
   ```bash
   docker logs grafana
   ```

4. 检查机器人是否被移出群聊或权限被撤销

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
- 检查机器人是否仍在群聊中

### 日志监控

```bash
# 查看 Grafana 告警日志
docker logs grafana 2>&1 | grep -i alert

# 查看 Prometheus 告警状态
curl http://localhost:9090/api/v1/alerts
```

## 安全注意事项

- Webhook URL 中的 access_token 是敏感信息，请妥善保管
- 定期轮换机器人 access_token
- 限制钉钉群的访问权限，只允许相关人员加入
- 监控告警消息的使用情况
- 设置机器人关键词过滤，避免误发消息

## 版本信息

- 钉钉开放平台 API: Latest
- Grafana: 12.3.0
- Prometheus: 2.53.2
- 配置版本: v1.0 (2025-12-15)
