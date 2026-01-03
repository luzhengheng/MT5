# TASK #004 同步指南

## 📦 变更清单

### 新增文件
- `scripts/verify_connection.py` - MT5 实时连接验证脚本
- `docs/archive/tasks/TASK_004_CONN_TEST/COMPLETION_REPORT.md` - 完成报告
- `docs/archive/tasks/TASK_004_CONN_TEST/QUICK_START.md` - 快速启动指南
- `docs/archive/tasks/TASK_004_CONN_TEST/VERIFY_LOG.log` - 验证日志
- `docs/archive/tasks/TASK_004_CONN_TEST/SYNC_GUIDE.md` - 本文件

### 修改文件
- `scripts/audit_current_task.py` - 新增 `audit_task_004()` 函数

---

## 🔧 环境依赖

### 必需依赖
确保以下包已安装：

```bash
# 安装 pyzmq (ZeroMQ Python 绑定)
pip install pyzmq

# 验证安装
python3 -c "import zmq; print(f'ZeroMQ: {zmq.zmq_version()}, PyZMQ: {zmq.pyzmq_version()}')"

# 预期输出
# ZeroMQ: 4.3.4, PyZMQ: 25.0.1 (或更新版本)
```

### 版本要求
- `pyzmq`: >= 24.0 (推荐最新)
- `Python`: >= 3.9
- `ZeroMQ`: >= 4.0 (系统级)

### 已有依赖
- `zmq` (通过 pyzmq 提供)
- `os`, `sys`, `time` (Python 标准库)
- `python-dotenv` (已安装，用于环境配置)

---

## 🌐 节点同步步骤

### 1. HUB 节点（Linux 代码仓库）
```bash
# 更新代码仓库
cd /opt/mt5-crs
git pull origin main

# 验证同步
ls -la scripts/verify_connection.py
ls -la docs/archive/tasks/TASK_004_CONN_TEST/
```

### 2. INF 节点（Linux 推理服务器）
```bash
# SSH 连接到 INF
ssh inf

# 同步代码
cd /opt/mt5-crs
git pull origin main

# 安装/更新依赖
pip install --upgrade pyzmq

# 验证安装
python3 -c "import zmq; print('✓ PyZMQ installed')"

# 验证脚本存在
test -f scripts/verify_connection.py && echo "✓ Script ready" || echo "✗ Missing"
```

### 3. GTW 节点（Windows 网关服务器）
**不需要 Python 客户端同步**，但需要：
- ✓ 确保 MT5 Server 运行在 172.19.141.255:5555
- ✓ 确保 EA 脚本返回 "OK_FROM_MT5" 握手字符串
- ✓ 检查防火墙规则：入站 TCP 5555 已开放

验证命令（Windows PowerShell）:
```powershell
# 检查端口开放
netstat -an | findstr "5555"
# 或
Get-NetTCPConnection -LocalPort 5555 -ErrorAction SilentlyContinue

# 检查防火墙规则
Get-NetFirewallRule -DisplayName "*5555*"

# 测试远程连接（从 Linux HUB）
# ping 172.19.141.255
# nc -zv 172.19.141.255 5555
```

### 4. GPU 节点（可选 - Linux 训练服务器）
**可选同步**，如需在 GPU 节点进行分布式连接测试:
```bash
ssh gpu

cd /opt/mt5-crs
git pull origin main

pip install --upgrade pyzmq

# 测试连接
python3 scripts/verify_connection.py
```

---

## ✅ 同步验证

在每个节点执行以下命令验证同步成功：

### HUB 节点
```bash
# [1] 检查脚本文件
test -f scripts/verify_connection.py && echo "✅ verify_connection.py exists" || echo "❌ Missing"

# [2] 检查审计脚本更新
grep -q "audit_task_004" scripts/audit_current_task.py && echo "✅ Audit updated" || echo "❌ Not updated"

# [3] 检查文档完整性
test -f docs/archive/tasks/TASK_004_CONN_TEST/COMPLETION_REPORT.md && echo "✅ Documentation complete" || echo "❌ Missing docs"

# [4] 检查 pyzmq 安装
python3 -c "import zmq; print('✅ pyzmq installed')" 2>/dev/null || echo "❌ pyzmq missing"

# [5] 运行脚本验证（可选，需要 Windows GTW 在线）
python3 scripts/verify_connection.py

# [6] 运行本地审计
python3 scripts/audit_current_task.py
```

### INF 节点
```bash
# 相同的验证步骤如上
python3 scripts/verify_connection.py
python3 scripts/audit_current_task.py
```

---

## 🚨 回滚计划

如需回滚到 TASK 003 状态：

```bash
# 查看提交历史
git log --oneline -10

# 查找 TASK 004 的提交哈希
git log --oneline --grep="004"

# 方案 1: Revert（推荐，保留历史）
git revert <TASK_004_COMMIT_HASH>

# 方案 2: Hard Reset（谨慎使用）
git reset --hard <TASK_003_COMMIT_HASH>

# 验证回滚
git log -1 --oneline
rm scripts/verify_connection.py
rm -rf docs/archive/tasks/TASK_004_CONN_TEST/
```

---

## 📝 配置变更

### 脚本参数

`scripts/verify_connection.py` 中的硬编码参数（TASK #004 要求）：

```python
# 目标地址（硬编码）
MT5_HOST = "172.19.141.255"
MT5_PORT = 5555

# 通信参数
TIMEOUT_MS = 5000  # 5 秒超时

# 测试消息
TEST_MESSAGE = "Hello"

# 预期响应
EXPECTED_RESPONSE = "OK_FROM_MT5"
```

### .env 无需修改

TASK #004 不修改 `.env` 文件，连接参数已硬编码在脚本中。

---

## 🔐 安全检查

- ✅ 无敏感信息泄露（客户端密钥、API 令牌等）
- ✅ 内网通信（TCP 172.19.x.x），无需 TLS
- ✅ 代码仅建立连接并验证握手，不执行交易
- ✅ 超时保护防止僵尸连接（5秒超时）
- ✅ 异常捕获防止程序崩溃
- ⚠️ 生产部署建议：
  - 启用 ZeroMQ 消息签名验证
  - 实施客户端 IP 白名单
  - 启用 ZeroMQ ZMTP-3.0 TLS 支持
  - 定期监控连接延迟
  - 实现连接池用于并发请求

---

## 📊 性能与网络影响

- **CPU 使用**: 极低（等待 I/O）
- **内存使用**: < 50MB
- **网络**: 单条 TCP 连接，每次测试 < 1KB 流量
- **延迟**: RTT < 100ms (局域网预期)
- **持续时间**: 单次测试约 5-10 秒

---

## 🔄 故障处理

### 如果 Windows GTW 离线
```
[✗] Connection timeout - no response from MT5 Server
```

**处理方式**:
- HUB/INF 节点会在 5 秒后超时并退出
- 日志中显示故障排查步骤
- 无需中断其他服务，等待 GTW 恢复后重试

### 如果防火墙规则缺失
```
[✗] Connection refused
```

**Windows GTW 上的解决方案**:
```powershell
# 通过 PowerShell 添加入站规则
New-NetFirewallRule -DisplayName "MT5 ZMQ (Task 004)" `
  -Direction Inbound `
  -LocalPort 5555 `
  -Protocol TCP `
  -Action Allow

# 或通过 GUI
# Control Panel > Windows Defender Firewall > Advanced Settings
# > Inbound Rules > New Rule > Port 5555 > Allow
```

### 如果 pyzmq 不可用
```
ModuleNotFoundError: No module named 'zmq'
```

**解决方案**:
```bash
pip install pyzmq
pip install --upgrade pyzmq

# 或指定版本
pip install "pyzmq>=24.0"
```

---

## 📋 部署检查清单

在执行双重门禁审查前，确认：

- [ ] `scripts/verify_connection.py` 已同步到所有 Linux 节点
- [ ] `scripts/audit_current_task.py` 已更新 `audit_task_004()` 函数
- [ ] `pyzmq` 已在所有 Linux 节点安装（>= 24.0）
- [ ] `docs/archive/tasks/TASK_004_CONN_TEST/` 目录完整
- [ ] VERIFY_LOG.log 包含 "OK_FROM_MT5" 指示符
- [ ] Windows GTW 已确认运行 MT5 Server (172.19.141.255:5555)
- [ ] 防火墙规则已配置允许端口 5555 TCP
- [ ] 网络连通性已验证 (ping 172.19.141.255)
- [ ] 本地审计 (Gate 1) 已通过 (6/6 检查)
- [ ] 外部审计 (Gate 2) 已通过

---

## 🚀 部署命令

快速部署脚本：

```bash
# 1. 同步代码
cd /opt/mt5-crs
git pull origin main

# 2. 验证依赖
python3 -c "import zmq; print(f'✓ PyZMQ {zmq.pyzmq_version()} ready')"

# 3. 运行本地审计 (Gate 1)
python3 scripts/audit_current_task.py

# 4. 如果 Gate 1 通过，运行双重门禁审查
python3 gemini_review_bridge.py

# 5. 如果都通过，自动提交
git status
```

---

**同步优先级**: 🔴 关键（阻塞后续任务）
**预计同步时间**: < 5 分钟（包括依赖检查）
**回滚难度**: 🟢 低（仅新增文件，无破坏性修改）
**风险等级**: 🟢 低（只读测试，不修改系统）

