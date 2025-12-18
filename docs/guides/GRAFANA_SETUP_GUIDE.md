# 📊 Grafana 仪表板配置指南

**文档版本**: v1.0  
**适用系统**: MT5-CRS 监控栈  
**前置条件**: Docker 已启动，Prometheus + Node Exporter 运行中

---

## 🚀 快速启动

### 1. 启动监控服务栈

```bash
# 启动 Docker（如果未运行）
systemctl start docker

# 进入配置目录
cd /root/M\ t\ 5-CRS/configs/docker

# 启动完整监控栈
docker compose -f docker-compose.mt5-hub.yml up -d

# 验证服务状态
docker ps | grep mt5-
```

**预期输出**:
```
mt5-grafana         运行中  0.0.0.0:3000->3000/tcp
mt5-prometheus      运行中  0.0.0.0:9090->9090/tcp
mt5-alertmanager    运行中  0.0.0.0:9093->9093/tcp
mt5-node-exporter   运行中  0.0.0.0:9100->9100/tcp
```

---

## 🔐 初次登录

1. **访问 Grafana**
   ```
   URL: http://localhost:3000
   或:  http://YOUR_SERVER_IP:3000
   ```

2. **默认凭据**
   ```
   用户名: admin
   密码:   MT5Hub@2025!Secure
   ```

3. **修改密码**（可选）
   - 首次登录后 Grafana 会提示修改密码
   - 建议设置强密码并记录到密码管理器

---

## 📡 配置 Prometheus 数据源

### 方法 1: 自动配置（推荐）

Grafana 已通过 `configs/grafana/provisioning/datasources/` 预配置 Prometheus。

验证配置:
```bash
# 检查数据源配置
ls -la /root/M\ t\ 5-CRS/configs/grafana/provisioning/datasources/

# 如果文件不存在，创建它
mkdir -p /root/M\ t\ 5-CRS/configs/grafana/provisioning/datasources/
cat > /root/M\ t\ 5-CRS/configs/grafana/provisioning/datasources/prometheus.yml << 'DATASOURCE'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://mt5-prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: 15s
      queryTimeout: 60s
DATASOURCE
```

### 方法 2: 手动配置

1. 登录 Grafana
2. 点击左侧 ⚙️ **Configuration** > **Data Sources**
3. 点击 **Add data source**
4. 选择 **Prometheus**
5. 配置:
   - **Name**: `Prometheus`
   - **URL**: `http://mt5-prometheus:9090`
   - **Access**: `Server (default)`
6. 点击 **Save & Test**

**预期结果**: ✅ Data source is working

---

## 📊 导入核心仪表板

### Dashboard 1: Node Exporter Full

**最佳选择**: Grafana 官方社区 Dashboard ID **1860**

```bash
# 通过 Grafana UI 导入
# 1. 点击左侧 + 按钮 > Import
# 2. 输入 Dashboard ID: 1860
# 3. 点击 Load
# 4. 选择 Prometheus 数据源
# 5. 点击 Import
```

**包含指标**:
- CPU 使用率（总体 + 每核）
- 内存使用（总量/已用/缓存）
- 磁盘 I/O（读写速率/IOPS）
- 网络流量（进/出）
- 系统负载（1/5/15 分钟）
- 文件系统使用率

---

### Dashboard 2: MT5 业务指标（自定义）

创建自定义 Dashboard 监控 MT5 特定业务指标：

```bash
# 创建 Dashboard JSON 文件
cat > /tmp/mt5_business_dashboard.json << 'DASHBOARD'
{
  "dashboard": {
    "title": "MT5 Trading System - Business Metrics",
    "panels": [
      {
        "title": "Data Pull Health",
        "targets": [
          {
            "expr": "up{job=\"mt5-data-pull\"}",
            "legendFormat": "Data Pull Status"
          }
        ],
        "type": "stat"
      },
      {
        "title": "Model Training Status",
        "targets": [
          {
            "expr": "up{job=\"mt5-training\"}",
            "legendFormat": "Training Status"
          }
        ],
        "type": "stat"
      },
      {
        "title": "System Alerts",
        "targets": [
          {
            "expr": "ALERTS{alertstate=\"firing\"}",
            "legendFormat": "{{alertname}}"
          }
        ],
        "type": "table"
      }
    ],
    "refresh": "30s",
    "time": {
      "from": "now-6h",
      "to": "now"
    }
  }
}
DASHBOARD

# 通过 Grafana UI 导入
# 1. 点击 + > Import
# 2. 上传 JSON 文件或粘贴内容
# 3. 选择 Prometheus 数据源
# 4. 点击 Import
```

---

### Dashboard 3: 基础设施概览

**推荐 Dashboard IDs**:
- **405**: Node Exporter Server Metrics
- **11074**: Node Exporter for Prometheus Dashboard
- **12486**: System Monitoring (资源详情)

导入方法同 Dashboard 1。

---

## 🔔 配置告警通知

### 1. 验证 Alertmanager 集成

```bash
# Grafana 已通过 Docker Compose 网络连接到 Alertmanager
# 验证连接
docker exec mt5-grafana ping -c 3 mt5-alertmanager
```

### 2. 添加通知渠道

1. 进入 **Alerting** > **Notification channels**
2. 点击 **New channel**
3. 配置钉钉 Webhook:
   - **Name**: `DingTalk Critical`
   - **Type**: `Webhook`
   - **URL**: `http://dingtalk-webhook-bridge:5001/webhook`
   - **HTTP Method**: `POST`
4. 测试通知并保存

---

## 📈 创建自定义告警规则

### 示例: 高 CPU 使用率告警

1. 进入任意 Dashboard
2. 编辑 Panel > 点击 **Alert** 标签
3. 创建告警规则:
   ```
   WHEN avg() OF query(A, 5m, now) IS ABOVE 80
   ```
4. 配置通知渠道
5. 保存 Dashboard

---

## 🔍 常用查询示例

### CPU 使用率
```promql
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

### 内存使用率
```promql
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

### 磁盘使用率
```promql
100 - ((node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100)
```

### 网络流量（入站）
```promql
rate(node_network_receive_bytes_total[5m])
```

### 告警触发数量
```promql
ALERTS{alertstate="firing"}
```

---

## 🛠️ 故障排查

### 问题 1: Grafana 无法访问

```bash
# 检查容器状态
docker ps | grep grafana

# 查看日志
docker logs mt5-grafana --tail 50

# 重启 Grafana
docker restart mt5-grafana
```

### 问题 2: Prometheus 数据源连接失败

```bash
# 测试网络连通性
docker exec mt5-grafana curl -s http://mt5-prometheus:9090/-/healthy

# 检查 Prometheus 状态
curl -s http://localhost:9090/-/healthy

# 预期输出: Prometheus is Healthy.
```

### 问题 3: 仪表板显示 "No data"

```bash
# 验证 Prometheus 正在抓取数据
curl -s "http://localhost:9090/api/v1/query?query=up" | jq

# 检查 Node Exporter
curl -s http://localhost:9100/metrics | head -20

# 验证时间范围（Grafana 右上角）
# 确保选择的时间范围内有数据
```

---

## 📚 推荐仪表板列表

| Dashboard ID | 名称 | 用途 |
|-------------|------|------|
| 1860 | Node Exporter Full | 服务器全面监控 |
| 405 | Node Exporter Server Metrics | 服务器基础指标 |
| 11074 | Node Exporter for Prometheus | 优化版 Node Exporter |
| 3662 | Prometheus 2.0 Overview | Prometheus 自身监控 |
| 9628 | Alertmanager | Alertmanager 监控 |

---

## 🎯 最佳实践

1. **仪表板组织**
   - 创建文件夹分类: Infrastructure / Business / Alerts
   - 使用标签标记 Dashboard

2. **性能优化**
   - 避免过于复杂的查询
   - 合理设置刷新间隔（推荐 30s-1m）
   - 使用变量参数化 Dashboard

3. **告警策略**
   - 关键指标设置多级阈值（warning/critical）
   - 避免告警疲劳（合理设置 repeat_interval）
   - 定期审查和调整告警规则

4. **备份**
   ```bash
   # 导出 Dashboard JSON
   # 通过 UI: Dashboard Settings > JSON Model > 复制
   
   # 备份 Grafana 数据
   docker exec mt5-grafana tar czf - /var/lib/grafana > grafana_backup_$(date +%Y%m%d).tar.gz
   ```

---

## 📞 支持信息

**文档位置**: `/tmp/GRAFANA_SETUP_GUIDE.md`  
**监控栈配置**: `configs/docker/docker-compose.mt5-hub.yml`  
**Prometheus 配置**: `configs/prometheus/prometheus.yml`  
**告警规则**: `configs/prometheus/rules/`

**相关服务端口**:
- Grafana: 3000
- Prometheus: 9090
- Alertmanager: 9093
- Node Exporter: 9100

---

**生成时间**: 2025-12-18  
**文档版本**: v1.0  
**维护者**: Claude AI + Grok AI 协同系统
