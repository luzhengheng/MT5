# Grafana 高级配置指南

## 概述

本指南介绍 MT5 Hub 项目中 Grafana 的高级配置，包括多数据源、自动配置加载、告警设置和权限管理。

## 架构设计

### 配置目录结构

```
configs/grafana/
├── grafana.ini              # 主配置文件
├── dashboards/              # Dashboard 模板
│   └── mt5_hub_kpi.json
└── provisioning/            # 自动配置
    ├── datasources/         # 数据源配置
    │   └── prometheus.yml
    └── notifiers/           # 告警通知器
        └── slack.yml
```

## 核心配置

### 1. 安全配置 (grafana.ini)

```ini
[security]
admin_password = MT5Hub@2025!Secure
disable_initial_admin_creation = true

[auth]
disable_login_form = false
anonymous_enabled = false
```

### 2. 多数据源配置

支持 Prometheus、Node Exporter、MT5 Metrics 等数据源：

- **Prometheus**: 核心指标数据源
- **Node Exporter**: 系统监控指标
- **MT5 Metrics**: 交易策略指标

### 3. 自动配置加载

通过 provisioning 目录实现配置的自动加载，无需手动配置数据源和通知器。

## Dashboard 特性

### MT5 Hub KPI Dashboard

包含以下关键指标：

1. **Sharpe Ratio**: 策略风险调整收益指标
2. **Data Freshness**: 数据新鲜度监控
3. **System Status**: 系统运行状态
4. **CPU/Memory Usage**: 系统资源监控
5. **Disk Usage**: 存储空间监控

### 变量支持

Dashboard 支持以下变量：
- `symbol`: 交易品种筛选
- `server`: 服务器节点筛选

## 告警配置

### Slack 集成

配置 Slack webhook 实现自动告警：
- 系统故障告警
- 性能阈值告警
- 数据异常告警

### 告警规则

支持的告警类型：
- CPU 使用率过高
- 内存不足
- 磁盘空间不足
- 服务不可用
- 数据延迟

## 访问方式

- **URL**: http://47.84.1.161:3000
- **用户名**: admin
- **密码**: MT5Hub@2025!Secure

## 维护指南

### 配置更新

1. 修改 `configs/grafana/` 下的配置文件
2. 重启 Grafana 容器：`docker restart grafana`
3. 验证配置生效

### 数据源管理

- 数据源配置通过 provisioning 自动加载
- 如需添加新数据源，编辑 `provisioning/datasources/` 下的文件

### Dashboard 管理

- Dashboard 通过 JSON 文件管理
- 支持版本控制和团队协作

## 故障排除

### 常见问题

1. **配置不生效**
   - 检查文件权限
   - 重启 Grafana 容器
   - 查看容器日志

2. **数据源连接失败**
   - 验证目标服务运行状态
   - 检查网络连通性
   - 确认认证信息

3. **告警不触发**
   - 检查告警规则配置
   - 验证通知器设置
   - 查看告警历史

## 性能优化

### 配置优化

- 使用 provisioning 避免手动配置
- 合理设置查询超时时间
- 配置适当的缓存策略

### 监控指标

- 监控 Grafana 本身的性能
- 跟踪查询响应时间
- 分析告警触发频率

## 安全注意事项

- 定期更新管理员密码
- 限制匿名访问
- 配置 HTTPS（生产环境）
- 定期审查用户权限

## 版本信息

- Grafana 版本: 12.3.0
- 配置版本: v2.0 (2025-12-14)
- 最后更新: 2025-12-14