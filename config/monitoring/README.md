# MT5-CRS 监控系统配置

## 概述

本目录包含 MT5-CRS 数据质量监控系统的配置文件，包括：

- **DQ Score 计算系统**: 5维度数据质量评分
- **Prometheus 指标导出器**: 将 DQ Score 导出为 Prometheus 可抓取的指标
- **Grafana 仪表盘**: 可视化数据质量监控
- **告警规则**: 自动化数据质量告警
- **健康检查脚本**: 系统健康状态检查

## 文件说明

### 1. `prometheus.yml`

**用途**: Prometheus 服务器配置文件

**配置内容**:
- 全局配置 (抓取间隔: 15s, 评估间隔: 15s)
- 告警管理器配置 (localhost:9093)
- 告警规则文件路径
- 抓取任务配置 (抓取 MT5-CRS DQ Score 指标)

**使用方法**:
```bash
# 启动 Prometheus
prometheus --config.file=/opt/mt5-crs/config/monitoring/prometheus.yml
```

### 2. `alert_rules.yml`

**用途**: Prometheus 告警规则定义

**包含告警**:
1. `LowDQScore` - 数据质量得分低于 70 分 (WARNING)
2. `CriticalDQScore` - 数据质量得分低于 50 分 (CRITICAL)
3. `LowCompletenessScore` - 完整性得分低于 80 分
4. `LowAccuracyScore` - 准确性得分低于 85 分
5. `LowTimelinessScore` - 及时性得分低于 60 分
6. `DQScoreDropping` - 平均 DQ Score 下降到 75 以下
7. `ExporterUnhealthy` - 导出器不健康
8. `AssetsCountAnomaly` - 监控资产数量异常
9. `RecordsCountDrop` - 数据记录数下降
10. `SystemicQualityIssue` - 系统性数据质量问题 (多个资产同时得分低)

**触发条件示例**:
- `LowDQScore`: 持续 5 分钟低于 70 分
- `CriticalDQScore`: 持续 2 分钟低于 50 分
- `SystemicQualityIssue`: 超过 3 个资产得分低于 70 分，持续 10 分钟

### 3. `grafana_dashboard_dq_overview.json`

**用途**: Grafana 仪表盘定义文件

**仪表盘面板**:
1. **平均 DQ Score** (Stat Panel)
   - 显示所有资产的平均 DQ Score
   - 阈值: <60 红色, 60-70 橙色, 70-80 黄色, >80 绿色

2. **监控资产数量** (Stat Panel)
   - 显示当前监控的资产数量

3. **导出器健康状态** (Stat Panel)
   - 显示 Prometheus 导出器健康状态
   - 0 = 不健康 (红色), 1 = 健康 (绿色)

4. **DQ Score 趋势** (Graph Panel)
   - 显示每个资产的 DQ Score 时间序列
   - 时间范围可调

5. **五维度得分对比** (Graph Panel)
   - 对比完整性、准确性、一致性、及时性、有效性
   - 显示各维度的平均得分

6. **各资产 DQ Score 排名** (Table Panel)
   - 表格显示各资产的 DQ Score
   - 按得分排序

**导入方法**:
1. 登录 Grafana
2. 导航到 Dashboards > Import
3. 上传 `grafana_dashboard_dq_overview.json` 文件
4. 选择 Prometheus 数据源
5. 点击 Import

## 快速开始

### 1. 启动 DQ Score 指标导出器

```bash
# 启动导出器 (HTTP 服务器在端口 9090)
python3 /opt/mt5-crs/src/monitoring/prometheus_exporter.py

# 后台运行
nohup python3 /opt/mt5-crs/src/monitoring/prometheus_exporter.py > /tmp/prometheus_exporter.log 2>&1 &
```

验证导出器运行:
```bash
# 检查健康状态
curl http://localhost:9090/health

# 查看指标
curl http://localhost:9090/metrics
```

### 2. 启动 Prometheus

```bash
# 启动 Prometheus (需要先安装 Prometheus)
prometheus --config.file=/opt/mt5-crs/config/monitoring/prometheus.yml
```

访问 Prometheus UI: http://localhost:9091

### 3. 配置 Grafana

```bash
# 启动 Grafana (需要先安装 Grafana)
systemctl start grafana-server
```

访问 Grafana UI: http://localhost:3000 (默认用户名/密码: admin/admin)

配置步骤:
1. 添加 Prometheus 数据源 (URL: http://localhost:9091)
2. 导入 `grafana_dashboard_dq_overview.json` 仪表盘

### 4. 运行健康检查

```bash
# 基本健康检查
python3 /opt/mt5-crs/bin/health_check.py

# 指定数据湖路径
python3 /opt/mt5-crs/bin/health_check.py --data-lake /opt/mt5-crs/data_lake

# 调整阈值
python3 /opt/mt5-crs/bin/health_check.py \
  --dq-warning 75 \
  --dq-critical 55 \
  --file-age-hours 48

# JSON 输出 (便于集成到监控系统)
python3 /opt/mt5-crs/bin/health_check.py --output json
```

健康检查退出码:
- `0`: 所有检查通过 (OK)
- `1`: 存在警告 (WARNING)
- `2`: 存在严重问题 (CRITICAL)

## DQ Score 计算方法

DQ Score 是一个 0-100 分的综合数据质量评分，由 5 个维度组成:

### 1. 完整性 (Completeness) - 权重 30%

- 缺失值比例
- 列完整性 (>95% 非缺失的列比例)
- 行完整性 (>90% 非缺失的行比例)

**计算公式**:
```
完整性得分 = (1 - 缺失率) * 50 + 优质列比例 * 30 + 优质行比例 * 20
```

### 2. 准确性 (Accuracy) - 权重 25%

- 无穷值检测
- 重复记录检测
- 异常值检测 (IQR 方法)

**计算公式**:
```
准确性得分 = (1 - 无穷值率) * 40 + (1 - 重复率) * 30 + (1 - 异常值率) * 30
```

### 3. 一致性 (Consistency) - 权重 20%

- 数据类型一致性
- 时间序列单调性
- 价格合理性检查

**计算公式**:
```
一致性得分 = 数据类型一致性 * 40 + 时间序列正确性 * 30 + 价格合理性 * 30
```

### 4. 及时性 (Timeliness) - 权重 15%

- 最新数据时间
- 数据更新频率

**计算公式**:
```
及时性得分 = f(最新数据距今天数)
- 1天内: 100分
- 2天: 90分
- 3天: 80分
- 7天: 60分
- >7天: 线性衰减到0
```

### 5. 有效性 (Validity) - 权重 10%

- 数值范围检查
- 业务规则验证

**计算公式**:
```
有效性得分 = 符合业务规则的记录比例 * 100
```

### 综合得分

```
DQ Score = 完整性 * 0.30 + 准确性 * 0.25 + 一致性 * 0.20 + 及时性 * 0.15 + 有效性 * 0.10
```

**得分等级**:
- A (85-100): 优秀
- B (70-84): 良好
- C (60-69): 中等
- D (50-59): 及格
- F (<50): 不及格

## 告警通知

### 配置 Alertmanager

编辑 Alertmanager 配置文件 (alertmanager.yml):

```yaml
route:
  receiver: 'email-notifications'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: 'email-notifications'
    email_configs:
      - to: 'your-email@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'password'
```

### 配置 Slack 通知

```yaml
receivers:
  - name: 'slack-notifications'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#data-quality-alerts'
        title: 'MT5-CRS Data Quality Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}: {{ .Annotations.description }}{{ end }}'
```

## 定期任务配置

### Cron 定时健康检查

编辑 crontab:
```bash
crontab -e
```

添加定时任务:
```cron
# 每小时运行健康检查
0 * * * * /usr/bin/python3 /opt/mt5-crs/bin/health_check.py --output json > /var/log/mt5-crs/health_check.log 2>&1

# 每天凌晨 2 点生成完整报告
0 2 * * * /usr/bin/python3 /opt/mt5-crs/bin/health_check.py > /var/log/mt5-crs/health_check_daily.log 2>&1
```

### Systemd 服务配置

创建 systemd 服务文件 `/etc/systemd/system/mt5-crs-exporter.service`:

```ini
[Unit]
Description=MT5-CRS Prometheus Exporter
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/opt/mt5-crs
ExecStart=/usr/bin/python3 /opt/mt5-crs/src/monitoring/prometheus_exporter.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mt5-crs-exporter
sudo systemctl start mt5-crs-exporter
sudo systemctl status mt5-crs-exporter
```

## 故障排查

### 问题 1: 导出器无法启动

**症状**: `ConnectionRefusedError` 或端口占用

**解决**:
```bash
# 检查端口是否被占用
lsof -i :9090

# 更换端口 (修改 prometheus_exporter.py)
# 或杀死占用端口的进程
kill -9 <PID>
```

### 问题 2: Prometheus 无法抓取指标

**症状**: Prometheus UI 显示 "DOWN"

**解决**:
```bash
# 检查导出器是否运行
curl http://localhost:9090/health

# 检查防火墙
sudo iptables -L | grep 9090

# 检查 Prometheus 配置
prometheus --config.file=prometheus.yml --config.check
```

### 问题 3: DQ Score 计算失败

**症状**: 指标显示 0 或 NaN

**解决**:
```bash
# 检查数据文件是否存在
ls -lh /opt/mt5-crs/data_lake/processed/features/

# 手动测试 DQ Score 计算
python3 -c "
from monitoring.dq_score import DQScoreCalculator
import pandas as pd

calculator = DQScoreCalculator()
df = pd.read_parquet('/opt/mt5-crs/data_lake/processed/features/AAPL.US_features.parquet')
score = calculator.calculate_dq_score(df)
print(score)
"
```

### 问题 4: Grafana 无法显示数据

**症状**: 仪表盘显示 "No Data"

**解决**:
1. 检查 Prometheus 数据源配置是否正确
2. 验证 PromQL 查询: `dq_score_total`
3. 检查时间范围是否合适
4. 确认指标名称与查询匹配

## 性能优化

### 1. 减少指标基数

如果监控的资产数量很多 (>100)，考虑:
- 聚合指标 (只保留平均值和异常资产)
- 使用时间序列数据库 (VictoriaMetrics, M3DB)

### 2. 调整抓取间隔

对于不需要实时监控的场景:
```yaml
scrape_configs:
  - job_name: 'mt5-crs-dq-score'
    scrape_interval: 5m  # 改为 5 分钟
```

### 3. 数据保留策略

设置 Prometheus 数据保留时间:
```bash
prometheus \
  --config.file=prometheus.yml \
  --storage.tsdb.retention.time=30d \
  --storage.tsdb.retention.size=10GB
```

## 相关文档

- [Prometheus 官方文档](https://prometheus.io/docs/)
- [Grafana 官方文档](https://grafana.com/docs/)
- [MT5-CRS 项目文档](../../README.md)
- [DQ Score 计算源码](../../src/monitoring/dq_score.py)
- [健康检查脚本](../../bin/health_check.py)

## 支持

如有问题，请:
1. 查看日志: `/var/log/mt5-crs/`
2. 运行健康检查: `python3 bin/health_check.py`
3. 提交 Issue: [GitHub Issues](https://github.com/your-repo/mt5-crs/issues)
