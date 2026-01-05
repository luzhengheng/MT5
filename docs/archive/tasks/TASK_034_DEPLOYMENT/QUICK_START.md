# TASK #034 快速开始指南
## 部署指南 - 5 分钟快速启动

**目的**: 将生产部署配置应用到 MT5-CRS 系统
**耗时**: ~15-20 分钟 (包括用户操作)
**难度**: 中等 (需要 root 权限)
**前置条件**: Ubuntu/Linux + sudo 权限 + DingTalk webhook URL

---

## 🎯 15 秒版概览

```bash
# 步骤 1: 获取 DingTalk Webhook URL
# (向群组管理员请求自定义机器人 webhook)

# 步骤 2: 更新环境配置
nano /opt/mt5-crs/.env
# 找到这一行并替换:
# DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=YOUR_ACTUAL_TOKEN

# 步骤 3: 一键部署
sudo bash /opt/mt5-crs/deploy_production.sh

# 步骤 4: 验证
python3 /opt/mt5-crs/scripts/uat_task_034.py
```

**预期结果**: 所有 8 个测试通过 ✅

---

## 📋 完整步骤指南

### 步骤 1: 检查前置条件 (2 分钟)

```bash
# 检查 Linux 版本
lsb_release -a
# 预期: Ubuntu 20.04+ 或 CentOS 8+

# 检查磁盘空间
df -h /opt/mt5-crs
# 预期: > 2GB 可用空间

# 检查内存
free -h
# 预期: > 2GB 可用内存

# 检查 Python 版本
python3 --version
# 预期: Python 3.9+

# 检查 git 安装
git --version
# 预期: git 2.x+
```

### 步骤 2: 获取 DingTalk Webhook (用户操作, 5 分钟)

**在 DingTalk 中:**

1. 打开 DingTalk 桌面应用
2. 找到目标群组 (例如 "MT5-CRS Risk Alerts")
3. 点击群组右上角设置 (三点菜单)
4. 选择 "��加机器人" 或 "集成"
5. 选择 "自定义 - 随时发送消息"
6. 设置机器人名称: `MT5-CRS Risk Monitor`
7. 启用签名验证: **勾选 "签名"**
8. 复制机器人生成的 webhook URL:
   ```
   https://oapi.dingtalk.com/robot/send?access_token=XXXXXXXXXXXXX
   ```
9. 同时复制生成的签名密钥 (格式: `SEC7d7cbd...`)

**URL 格式检查**:
```
✅ https://oapi.dingtalk.com/robot/send?access_token=...
❌ 不应有任何空格或不完整的 URL
```

### 步骤 3: 更新环境配置 (2 分钟)

```bash
# 打开 .env 文件编辑
cd /opt/mt5-crs
nano .env

# 找到这些行并更新:
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=YOUR_ACTUAL_TOKEN
DINGTALK_SECRET=SEC7d7cbd2505332b3ed3053f87dadfd2bbac9b0c2ba46d63d7c587351f3bb08de5

# 保存: Ctrl+O, Enter, Ctrl+X

# 验证更新成功
grep DINGTALK /opt/mt5-crs/.env
# 预期: 两行都显示真实值 (不是占位符)
```

### 步骤 4: 验证安全权限 (1 分钟)

```bash
# 确保 .env 文件权限正确 (仅用户读写)
chmod 600 /opt/mt5-crs/.env

# 验证权限
ls -l /opt/mt5-crs/.env
# 预期: -rw------- 1 root root

# 确保目录结构完整
ls -la /opt/mt5-crs/
# 预期: 包含 scripts/, src/, docs/ 目录
```

### 步骤 5: 执行 Gate 1 审计 (2 分钟)

```bash
cd /opt/mt5-crs

# 运行自动审计
python3 scripts/audit_task_034.py

# 预期输出:
# ✅ GATE 1 AUDIT: PASSED
# Total Checks: 54
# Passed: 54
# Failed: 0
# Success Rate: 54/54 (100%)
```

**如果失败**: 检查输出中的红色 ❌ 项，修复问题后重新运行

### 步骤 6: 执行 Gate 2 架构审查 (1 分钟)

```bash
cd /opt/mt5-crs

# 运行 AI 架构审查
python3 gemini_review_bridge.py

# 预期输出:
# 🛡️ Gemini Review Bridge v3.5
# ✅ AI Review: PASSED
# Confidence: ⭐⭐⭐⭐⭐
```

**如果失败**: 检查 API 密钥配置或网络连接

### 步骤 7: 执行一键部署 (5 分钟)

```bash
cd /opt/mt5-crs

# 以 root 权限运行部署脚本
sudo bash deploy_production.sh

# 预期步骤:
# Step 1: 准备环境 ✅
# Step 2: 生成 htpasswd ✅
# Step 3: 部署 Nginx 配置 ✅
# Step 4: 验证部署 ✅
# Step 5: 启动 Streamlit 服务 ✅

# 预期最后输出:
# ✅ DEPLOYMENT COMPLETE
# Dashboard Access:
#   URL: http://www.crestive.net
#   Username: admin
#   Password: ******* (stored in htpasswd)
```

**关键步骤说明**:

| 步骤 | 说明 | 预期结果 |
|------|------|---------|
| Step 1 | 环境准备 (验证 root, 备份 .env) | 无错误 |
| Step 2 | 生成 htpasswd 文件 | `/etc/nginx/.htpasswd` 已创建 |
| Step 3 | Nginx 配置部署 | 配置文件已复制到 sites-available/ |
| Step 4 | Nginx 验证和重载 | Nginx 监听端口 80 |
| Step 5 | Streamlit 启动 | 进程运行在端口 8501 |

### 步骤 8: 验证部署 (3 分钟)

```bash
cd /opt/mt5-crs

# 运行完整的 UAT 测试套件
python3 scripts/uat_task_034.py

# 预期: 8/8 测试通过
# ✅ Test 1: Dashboard Access - PASS
# ✅ Test 2: Authenticated Access - PASS
# ✅ Test 3: DingTalk Configuration - PASS
# ✅ Test 4: Send Real Alert - PASS
# ✅ Test 5: Kill Switch Alert - PASS
# ✅ Test 6: Dashboard URL Validation - PASS
# ✅ Test 7: Nginx Proxy Configuration - PASS
# ✅ Test 8: Streamlit Service - PASS

# 最后输出:
# ✅ ALL UAT TESTS PASSED
```

### 步骤 9: 在浏览器中测试 (2 分钟)

```
1. 打开浏览器访问: http://www.crestive.net
2. 输入凭证:
   用户名: admin
   密码: MT5Hub@2025!Secure
3. 应该看到 MT5-CRS 仪表板，包含:
   - 实时 PnL 和头寸
   - 应急开关状态
   - 交易历史
   - 风险管理面板
```

### 步骤 10: 验证 DingTalk 集成 (1 分钟)

```
1. 打开 DingTalk 应用
2. 进入 "MT5-CRS Risk Alerts" 群组
3. 查找来自 "MT5-CRS Risk Monitor" 机器人的消息
4. 应该看到测试告警卡片

如果看不到消息:
  - 检查 webhook URL 是否正确
  - 查看日志: tail -50 /opt/mt5-crs/var/logs/streamlit.log
```

---

## 🚨 常见问题与解决

### 问题 1: "Permission denied" (权限错误)

```bash
# 症状: sudo bash deploy_production.sh 失败

# 解决:
sudo chmod +x /opt/mt5-crs/deploy_production.sh
sudo bash /opt/mt5-crs/deploy_production.sh
```

### 问题 2: "Port 80 already in use" (端口被占用)

```bash
# 症状: Nginx 无法启动

# 查看谁在使用端口 80:
sudo lsof -i :80

# 杀死冲突的进程 (如果是旧 Nginx):
sudo systemctl stop nginx
sudo systemctl kill nginx
sudo systemctl start nginx
```

### 问题 3: "htpasswd: command not found" (缺少工具)

```bash
# 症状: htpasswd 命令不存在

# 解决: 脚本会自动安装
# 如果手动安装:
sudo apt-get update
sudo apt-get install -y apache2-utils
```

### 问题 4: "DINGTALK_WEBHOOK_URL not set" (DingTalk 配置缺失)

```bash
# 症状: DingTalk 测试失败

# 解决:
# 1. 确认 webhook URL 已获取
# 2. 更新 .env: nano /opt/mt5-crs/.env
# 3. 使用 grep 验证:
grep "DINGTALK_WEBHOOK_URL" /opt/mt5-crs/.env
# 应该显示完整的 URL (不是占位符)
```

### 问题 5: "Connection refused" (连接拒绝)

```bash
# 症状: 无法访问 http://www.crestive.net

# 解决:
# 1. 检查 Nginx 状态
sudo systemctl status nginx
# 预期: active (running)

# 2. 检查 Streamlit 状态
pgrep -f "streamlit run"
# 预期: 显示进程 ID

# 3. 检查日志
tail -50 /var/log/nginx/dashboard_error.log
tail -50 /opt/mt5-crs/var/logs/streamlit.log
```

---

## ✅ 验证清单

部署完成后，确保:

- [ ] Gate 1 审计: 54/54 通过
- [ ] Gate 2 审查: AI 已批准
- [ ] 所有 8 个 UAT 测试: 通过
- [ ] 浏览器访问: http://www.crestive.net 可访问
- [ ] 需要身份验证: 输入用户名/密码后访问
- [ ] DingTalk 消息: 在群组中收到测试消息
- [ ] Nginx 日志: 无错误
- [ ] Streamlit 日志: 无错误

---

## 📞 支持与监控

### 立即监控 (部署后)

```bash
# 实时监控 Nginx 访问日志
tail -f /var/log/nginx/dashboard_access.log

# 实时监控 Streamlit 日志
tail -f /opt/mt5-crs/var/logs/streamlit.log

# 检查服务状态
systemctl status nginx
pgrep -f "streamlit run"
```

### 24 小时监控任务

- [ ] 每小时检查一次日志是否有错误
- [ ] 验证 DingTalk 通知是否正常发送
- [ ] 监控仪表板是否响应正常
- [ ] 记录任何异常情况

### 故障恢复

如果部署失败或需要回滚:

```bash
# 停止服务
sudo systemctl stop nginx
pkill -f "streamlit run"

# 恢复之前的 .env
cp /opt/mt5-crs/.env.backup /opt/mt5-crs/.env

# 删除 Nginx 配置
sudo rm /etc/nginx/sites-enabled/dashboard
sudo rm /etc/nginx/sites-available/dashboard

# 测试并重新加载 Nginx
sudo nginx -t
sudo systemctl reload nginx

# 重新启动应用
cd /opt/mt5-crs
nohup streamlit run src/dashboard/app.py &
```

---

## 🎓 学习资源

### 部署相关文档

- **完整部署指南**: DEPLOYMENT_GUIDE.md (18.4KB)
  - 详细的系统要求
  - 故障排除指南
  - 安全最佳实践
  - 监控程序

- **密钥管理指南**: SECRETS_MANAGEMENT.md (18.7KB)
  - DingTalk webhook 获取步骤
  - 90 天轮换计划
  - 事件响应程序
  - 合规性检查清单

- **验证清单**: VERIFICATION_CHECKLIST.md (17.9KB)
  - 100+ 验证项
  - 端到端流程检查
  - 安全验证
  - 性能检查

### 技术细节

- **实现摘要**: IMPLEMENTATION_SUMMARY.md (21.8KB)
  - Nginx 配置详解
  - 部署脚本说明
  - 集成点验证
  - 质量指标

---

## 🎉 成功标志

**部署成功时，应该看到:**

```
✅ GATE 1 AUDIT: PASSED (54/54 checks)
✅ GATE 2 REVIEW: APPROVED (⭐⭐⭐⭐⭐)
✅ UAT TESTS: 8/8 PASSED
✅ Dashboard: Accessible via http://www.crestive.net
✅ DingTalk: Notifications received in group chat
✅ Services: Nginx + Streamlit running
✅ Logs: No errors in error logs
```

---

**预计完成时间**: 15-20 分钟
**难度等级**: 中等 (需要 root 权限)
**最后更新**: 2026-01-05
**文档版本**: 1.0
