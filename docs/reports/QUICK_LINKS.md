# 🔗 快速访问链接

> 这些链接会自动指向 `dev-env-reform-v1.0` 分支的最新版本

## 📋 核心报告

| 文档 | GitHub 链接 |
|------|-----------|
| **AI 协同工作报告** | https://raw.githubusercontent.com/luzhengheng/MT5/dev-env-reform-v1.0/docs/reports/for_grok.md |
| **监控告警部署报告** | https://raw.githubusercontent.com/luzhengheng/MT5/dev-env-reform-v1.0/docs/reports/MONITORING_ALERT_DEPLOYMENT_REPORT.md |

## 🔧 配置文件

| 配置 | 用途 | GitHub 链接 |
|------|------|-----------|
| **Prometheus 主配置** | 指标收集与告警规则加载 | https://raw.githubusercontent.com/luzhengheng/MT5/dev-env-reform-v1.0/configs/prometheus/prometheus.yml |
| **基础设施告警规则** | 9条基础设施监控规则 | https://raw.githubusercontent.com/luzhengheng/MT5/dev-env-reform-v1.0/configs/prometheus/rules/infrastructure.yml |
| **业务告警规则** | 9条业务流程监控规则 | https://raw.githubusercontent.com/luzhengheng/MT5/dev-env-reform-v1.0/configs/prometheus/rules/business.yml |
| **Alertmanager 配置** | 告警路由与接收器配置 | https://raw.githubusercontent.com/luzhengheng/MT5/dev-env-reform-v1.0/configs/alertmanager/alertmanager.yml |

## 💻 脚本文件

| 脚本 | 功能 | GitHub 链接 |
|------|------|-----------|
| **钉钉 Webhook 桥接** | 告警转发到钉钉群 | https://raw.githubusercontent.com/luzhengheng/MT5/dev-env-reform-v1.0/scripts/monitor/dingtalk_webhook_bridge.py |
| **SSH 密钥统一脚本** | 分发 SSH 公钥到所有服务器 | https://raw.githubusercontent.com/luzhengheng/MT5/dev-env-reform-v1.0/scripts/setup/unify_ssh_keys.sh |
| **防火墙配置脚本** | 自动化防火墙规则设置 | https://raw.githubusercontent.com/luzhengheng/MT5/dev-env-reform-v1.0/scripts/setup/configure_firewall.sh |

## ⚙️ 系统服务

| 服务 | 功能 | 位置 |
|------|------|------|
| **DingTalk Webhook Bridge** | 监听 5001 端口，转发告警消息 | `/etc/systemd/system/dingtalk-webhook-bridge.service` |

## 📊 实时查看

### 本地访问
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093
- **Node Exporter**: http://localhost:9100
- **钉钉 Webhook**: http://localhost:5001/health

---

**更新时间**: 自动同步
**分支**: dev-env-reform-v1.0
**仓库**: https://github.com/luzhengheng/MT5
