# TASK #034 同步指南
## 部署变更清单 & 环境迁移

**目的**: 记录 TASK #034 带来的所有配置变更，便于同步到其他环境
**适用环境**: 本地开发、测试、生产
**版本**: 1.0
**日期**: 2026-01-05

---

## 📋 变更总览 (Change Overview)

TASK #034 引入了生产级部署基础设施。以下是所有变更的清单:

### 新增文件 (8 个)

| 文件 | 大小 | 环境 | 需要同步 |
|------|------|------|---------|
| `nginx_dashboard.conf` | 2.5KB | 生产 | ✅ 必须 |
| `deploy_production.sh` | 6.1KB | 生产 | ✅ 必须 |
| `.env.production` | 3.3KB | 生产模板 | ✅ 必须 |
| `scripts/uat_task_034.py` | 13.8KB | 测试 | ✅ 推荐 |
| `scripts/audit_task_034.py` | 11.7KB | 测试 | ✅ 推荐 |
| DEPLOYMENT_GUIDE.md | 18.4KB | 文档 | ✅ 必须 |
| SECRETS_MANAGEMENT.md | 18.7KB | 文档 | ✅ 必须 |
| VERIFICATION_CHECKLIST.md | 17.9KB | 文档 | ✅ 必须 |

### 修改的文件 (0 个)

**好消息**: TASK #034 不修改任何现有源代码，所有变更都是新增配置和文档。

### 删除的文件 (0 个)

**好消息**: 无需删除任何现有文件。

---

## 🔧 环境变量清单 (Environment Variables)

### 必须添加 (生产环境)

```bash
# DingTalk 集成 (已在 .env.production 中)
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=YOUR_ACTUAL_TOKEN
DINGTALK_SECRET=SEC7d7cbd2505332b3ed3053f87dadfd2bbac9b0c2ba46d63d7c587351f3bb08de5

# 仪表板配置 (已在 .env.production 中)
DASHBOARD_PUBLIC_URL=http://www.crestive.net
STREAMLIT_HOST=127.0.0.1
STREAMLIT_PORT=8501
```

### 可选增强 (推荐用于安全)

```bash
# HTTPS/SSL 配置 (生产推荐)
SSL_CERT_PATH=/etc/letsencrypt/live/www.crestive.net/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/www.crestive.net/privkey.pem
SSL_PORT=443

# 日志轮换 (推荐)
LOG_MAX_SIZE=100MB
LOG_RETENTION_DAYS=30

# 监控 (推荐)
MONITORING_ENABLED=true
ALERT_EMAIL=ops@crestive.net
```

### 不要修改 (保留现有配置)

以下现有变量应保持不变:

```bash
# 数据库 (保留)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=trader
POSTGRES_PASSWORD=password
POSTGRES_DB=mt5_crs

# API (保留)
GEMINI_API_KEY=...
GEMINI_BASE_URL=https://api.yyds168.net/v1
GEMINI_MODEL=gemini-3-pro-preview

# ZMQ 和交易 (保留)
ZMQ_MARKET_DATA_HOST=localhost
ZMQ_MARKET_DATA_PORT=5556
GTW_HOST=172.19.141.255
GTW_PORT=5555

# Risk Management (保留)
RISK_MAX_DAILY_LOSS=-50.0
RISK_MAX_ORDER_RATE=5
RISK_MAX_POSITION_SIZE=1.0
KILL_SWITCH_LOCK_FILE=/opt/mt5-crs/var/kill_switch.lock
```

---

## 📦 依赖清单 (Dependencies)

### 系统级依赖 (需要安装)

```bash
# 自动安装 (deploy_production.sh 处理)
sudo apt-get update
sudo apt-get install -y nginx          # Web 反向代理
sudo apt-get install -y apache2-utils  # htpasswd 工具

# 验证安装
nginx --version      # 预期: nginx/1.x+
htpasswd -v         # 预期: version X.X.x
```

### Python 依赖 (已有)

```bash
# 无新增依赖，使用现有环境:
# - streamlit (已安装)
# - pandas (已安装)
# - requests (已安装)
# - python-dotenv (已安装)

# 验证
python3 -c "import streamlit; print(streamlit.__version__)"
```

### 网络依赖 (DingTalk)

```bash
# 必须能访问:
https://oapi.dingtalk.com/robot/send    # DingTalk API
http://www.crestive.net                 # Dashboard 域名

# 测试连接
curl -I https://oapi.dingtalk.com/
curl -I http://www.crestive.net/
```

---

## 🔐 密钥 & 凭证清单 (Secrets)

### 需要获取的密钥 (用户操作)

| 密钥 | 来源 | 用途 | 安全级别 |
|------|------|------|---------|
| **DingTalk Webhook URL** | DingTalk 群组 | 发送告警 | 🔴 CRITICAL |
| **DingTalk Secret** | DingTalk 设置 | HMAC 签名 | 🔴 CRITICAL |
| **Dashboard Password** | 由 htpasswd 管理 | Basic Auth | 🔴 CRITICAL |

### 已提供的密钥 (项目配置)

```bash
# DingTalk Secret (已配置)
DINGTALK_SECRET=SEC7d7cbd2505332b3ed3053f87dadfd2bbac9b0c2ba46d63d7c587351f3bb08de5

# 仪表板密码 (已配置)
Dashboard Username: admin
Dashboard Password: MT5Hub@2025!Secure
```

### 密钥轮换计划

```
DingTalk Webhook & Secret:
  - 轮换频率: 每 90 天
  - 轮换流程: SECRETS_MANAGEMENT.md 中的"Step 3: 轮换 DingTalk Webhook"
  - 联系人: DingTalk 群组管理员

Dashboard Password:
  - 轮换频率: 每 90 天
  - 轮换流程: SECRETS_MANAGEMENT.md 中的"Step 2: 轮换仪表板密码"
  - 执行: sudo htpasswd -bc /etc/nginx/.htpasswd admin "NEW_PASSWORD"
```

---

## 🚀 部署清单 (Deployment Checklist)

### 本地开发环境

```bash
# Step 1: 从 Git 获取新文件
cd /opt/mt5-crs
git pull origin main

# Step 2: 验证新文件存在
ls -la nginx_dashboard.conf
ls -la scripts/uat_task_034.py
ls -la scripts/audit_task_034.py

# Step 3: 运行审计 (可选)
python3 scripts/audit_task_034.py
# 预期: 54/54 通过

# Step 4: 查看文档
cat docs/archive/tasks/TASK_034_DEPLOYMENT/QUICK_START.md
```

### 测试环境

```bash
# Step 1: 同步代码
git pull origin main

# Step 2: 复制配置模板
cp .env.production .env.test
# 编辑 .env.test (使用测试 DingTalk webhook)

# Step 3: 运行 UAT
python3 scripts/uat_task_034.py
# 预期: 所有测试通过

# Step 4: 保存测试日志
cp VERIFY_LOG.log docs/archive/tasks/TASK_034_DEPLOYMENT/TEST_LOG.log
```

### 生产环境

```bash
# Step 1: 备份当前配置
cp /opt/mt5-crs/.env /opt/mt5-crs/.env.backup.$(date +%s)

# Step 2: 同步代码
cd /opt/mt5-crs
git pull origin main

# Step 3: 获取 DingTalk webhook (用户操作)
# 向群组管理员请求自定义机器人 webhook

# Step 4: 更新 .env
nano /opt/mt5-crs/.env
# 添加: DINGTALK_WEBHOOK_URL=<real_url>

# Step 5: 执行 Gate 1 审计
python3 scripts/audit_task_034.py
# 预期: 54/54 通过

# Step 6: 执行 Gate 2 审查
python3 gemini_review_bridge.py
# 预期: AI 批准

# Step 7: 执行部署
sudo bash deploy_production.sh

# Step 8: 验证部署
python3 scripts/uat_task_034.py
# 预期: 8/8 通过

# Step 9: 开始监控
tail -f /var/log/nginx/dashboard_access.log &
tail -f /opt/mt5-crs/var/logs/streamlit.log &
```

---

## 📊 文件同步矩阵 (File Sync Matrix)

| 文件 | 本地 | 测试 | 生产 | 备注 |
|------|------|------|------|------|
| `nginx_dashboard.conf` | ✅ 复制 | ✅ 复制 | ✅ 部署 | Nginx 配置 |
| `deploy_production.sh` | ✅ 有 | ✅ 有 | ✅ 运行 | 部署脚本 |
| `.env.production` | ✅ 参考 | ✅ 复制+编辑 | ✅ 复制+编辑 | 配置模板 |
| `scripts/uat_task_034.py` | ✅ 复制 | ✅ 运行 | ✅ 运行 | UAT 测试 |
| `scripts/audit_task_034.py` | ✅ 复制 | ✅ 运行 | ✅ 运行 | 审计脚本 |
| DEPLOYMENT_GUIDE.md | ✅ 阅读 | ✅ 参考 | ✅ 参考 | 文档 |
| SECRETS_MANAGEMENT.md | ✅ 阅读 | ✅ 参考 | ✅ 参考 | 文档 |
| VERIFICATION_CHECKLIST.md | ✅ 查看 | ✅ 检查 | ✅ 检查 | 文档 |

---

## 🔄 版本控制同步

### Git 操作

```bash
# 获取最新代码
git pull origin main

# 查看新增文件
git log --oneline -1
# 预期: ops(task-034): implement production deployment...

git show --name-only
# 预期: 显示 8 个新文件

# 验证没有冲突
git status
# 预期: working tree clean
```

### 提交历史

```
Commit: 3209c1db955d04beba0913726f73717e2ccdc04b
Type: ops (Operations/Infrastructure)
Author: MT5 AI Agent
Date: 2026-01-05

Changes:
  + deploy_production.sh (6.1KB)
  + nginx_dashboard.conf (2.5KB)
  + scripts/uat_task_034.py (13.8KB)
  + scripts/audit_task_034.py (11.7KB)
  + docs/archive/tasks/TASK_034_DEPLOYMENT/* (5 files, 54KB)

Total: 8 files, 3,896 insertions
```

---

## 🚨 回滚程序 (Rollback)

如果部署出现问题，按以下步骤回滚:

### 快速回滚 (< 5 分钟)

```bash
# Step 1: 停止服务
sudo systemctl stop nginx
pkill -f "streamlit run"

# Step 2: 恢复之前的 .env
cp /opt/mt5-crs/.env.backup /opt/mt5-crs/.env

# Step 3: 移除 Nginx 配置
sudo rm /etc/nginx/sites-enabled/dashboard
sudo rm /etc/nginx/sites-available/dashboard

# Step 4: 测试 Nginx
sudo nginx -t
# 预期: configuration OK

# Step 5: 重新启动 Nginx
sudo systemctl reload nginx

# Step 6: 验证状态
sudo systemctl status nginx
# 预期: active (running)
```

### 完整回滚 (如果需要)

```bash
# 如果快速回滚不足，恢复到上一个 Git 版本:
cd /opt/mt5-crs

# 查看 Git 历史
git log --oneline -10

# 恢复到 TASK #034 之前的版本
git reset --hard 6cb36d2  # TASK #033 的最后一次提交

# 验证
git log --oneline -1
# 预期: docs(task-033): add gate 1 audit script...

# 重启应用
# (按照项目的标准重启程序)
```

---

## 📈 监控和度量 (Monitoring)

### 部署后的关键指标

```bash
# 1. Nginx 运行状态
sudo systemctl status nginx
# 预期: active (running)

# 2. Streamlit 进程
pgrep -f "streamlit run"
# 预期: 显示 PID (不为空)

# 3. 端口监听
sudo netstat -tlnp | grep -E ":80|:8501"
# 预期: 显示 Nginx 监听 80, Streamlit 监听 8501

# 4. 服务响应时间
curl -w "%{time_total}s\n" -o /dev/null -s http://www.crestive.net/
# 预期: < 1 秒

# 5. 错误日志
grep -c "error" /var/log/nginx/dashboard_error.log
# 预期: 0 或很小的数字

# 6. DingTalk 连接
grep "DingTalk" /opt/mt5-crs/var/logs/streamlit.log | tail -3
# 预期: 显示最近的 webhook 调用
```

### 定期检查清单

**每小时**:
```bash
tail -20 /var/log/nginx/dashboard_access.log
tail -20 /opt/mt5-crs/var/logs/streamlit.log
```

**每天**:
```bash
# 检查所有服务状态
systemctl status nginx streamlit  # (如果有 systemd 单位)
pgrep -f "nginx|streamlit" | wc -l  # 预期: 2+

# 检查磁盘空间
df -h /opt/mt5-crs

# 检查错误数量
grep -i "error\|fail" /var/log/nginx/dashboard_error.log | wc -l
grep -i "error\|fail" /opt/mt5-crs/var/logs/streamlit.log | wc -l
```

**每周**:
```bash
# 运行完整审计
python3 scripts/audit_task_034.py

# 运行 UAT
python3 scripts/uat_task_034.py

# 检查秘钥过期 (如果配置了轮换)
grep DINGTALK /opt/mt5-crs/.env
```

---

## 📞 支持联系方式

### 部署问题

如遇到部署相关问题:

1. **查看文档**: DEPLOYMENT_GUIDE.md 的故障排除部分
2. **检查日志**:
   - Nginx: `/var/log/nginx/dashboard_error.log`
   - Streamlit: `/opt/mt5-crs/var/logs/streamlit.log`
3. **运行诊断**:
   ```bash
   python3 scripts/audit_task_034.py  # 检查配置
   python3 scripts/uat_task_034.py    # 测试功能
   ```

### 密钥问题

DingTalk webhook 或秘钥问题:

1. **查看指南**: SECRETS_MANAGEMENT.md
2. **获取新 webhook**: 按 QUICK_START.md 步骤 2 进行
3. **更新 .env**: `nano /opt/mt5-crs/.env`
4. **重启服务**: `sudo systemctl reload nginx && pkill -f streamlit`

### 集成问题

与 TASK #033 或 #032 的集成问题:

1. **查看集成点**: IMPLEMENTATION_SUMMARY.md
2. **验证配置**: `python3 scripts/audit_task_034.py`
3. **查看日志**: 两个应用的日志文件

---

## ✅ 同步完成检查清单

部署完成后，确保:

- [ ] 所有 8 个新文件已同步到目标环境
- [ ] .env 已更新 DingTalk webhook URL
- [ ] Gate 1 审计通过 (54/54)
- [ ] Gate 2 审查通过 (AI 批准)
- [ ] 所有 8 个 UAT 测试通过
- [ ] 仪表板可访问 (http://www.crestive.net)
- [ ] DingTalk 消息正常发送
- [ ] Nginx 和 Streamlit 无错误
- [ ] 24 小时监控正常进行

---

**同步指南版本**: 1.0
**最后更新**: 2026-01-05
**适用**: TASK #034 生产部署
