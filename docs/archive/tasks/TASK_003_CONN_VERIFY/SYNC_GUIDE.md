# TASK #003 同步指南

## 📦 变更清单

### 新增文件
- `src/client/mt5_connector.py` - MT5 ZeroMQ 客户端
- `docs/archive/tasks/TASK_003_CONN_VERIFY/COMPLETION_REPORT.md` - 完成报告
- `docs/archive/tasks/TASK_003_CONN_VERIFY/QUICK_START.md` - 快速启动指南
- `docs/archive/tasks/TASK_003_CONN_VERIFY/VERIFY_LOG.log` - 验证日志
- `docs/archive/tasks/TASK_003_CONN_VERIFY/SYNC_GUIDE.md` - 本文件

### 修改文件
- `.env` - 新增 MT5 ZeroMQ 配置
- `scripts/audit_current_task.py` - 新增 `audit_task_003()` 函数

---

## 🔧 环境依赖

### 新增依赖
必须安装 `pyzmq`:

```bash
# 安装 pyzmq
pip install pyzmq

# 或使用 pip3
pip3 install pyzmq

# 验证安装
python3 -c "import zmq; print(zmq.__version__)"
```

### 已有依赖
- python-dotenv (已安装)
- os, sys, time (stdlib)

### 依赖版本
- pyzmq: >= 24.0 (推荐最新)
- Python: >= 3.9

---

## 🌐 节点同步步骤

### 1. HUB 节点（代码仓库 - Linux）
```bash
cd /opt/mt5-crs
git pull origin main
```

验证:
```bash
ls -la src/client/mt5_connector.py
grep MT5_HOST .env
```

### 2. INF 节点（推理服务器 - Linux）
```bash
ssh inf

cd /opt/mt5-crs
git pull origin main

# 安装依赖
pip install pyzmq

# 验证安装
python3 src/client/mt5_connector.py --help 2>/dev/null || echo "Ready for testing"
```

### 3. GTW 节点（Windows 网关 - Windows Server 2022）
**不需要 Python 客户端同步**，但需要：
- 确保 MT5 Server 运行在监听状态
- 检查防火墙规则：入站 5555 端口已开放
- 验证命令:
  ```cmd
  netstat -an | find "5555"
  ```

### 4. GPU 节点（训练服务器 - Linux）
**可选同步**，如需在 GPU 节点进行分布式连接测试:
```bash
ssh gpu

cd /opt/mt5-crs
git pull origin main

pip install pyzmq

# 测试连接
python3 src/client/mt5_connector.py
```

---

## ✅ 同步验证

在每个节点执行以下命令验证同步成功：

```bash
# [1] 检查文件存在性
test -f src/client/mt5_connector.py && echo "✅ mt5_connector.py exists" || echo "❌ Missing"

# [2] 检查审计脚本更新
grep -q "audit_task_003" scripts/audit_current_task.py && echo "✅ Audit updated" || echo "❌ Not updated"

# [3] 检查 .env 配置
grep -q "MT5_HOST" .env && echo "✅ MT5 config added" || echo "❌ Not configured"

# [4] 检查 pyzmq 安装
python3 -c "import zmq; print('✅ pyzmq installed')" 2>/dev/null || echo "❌ pyzmq missing"

# [5] 运行审计
python3 scripts/audit_current_task.py
```

---

## 🚨 回滚计划

如需回滚到 Task 022 状态：

```bash
# 查看提交历史
git log --oneline -5

# 查找 Task 003 的提交哈希
git log --oneline --grep="003" --grep="Connection"

# 回滚方案 1：Revert（推荐，保留历史）
git revert <TASK_003_COMMIT_HASH>

# 回滚方案 2：Hard Reset（谨慎使用）
git reset --hard <TASK_022_COMMIT_HASH>
```

---

## 📝 配置变更

### .env 变更

```diff
# 新增配置段
+ # ============================================================================
+ # MT5 ZeroMQ Gateway Configuration (Task #003)
+ # ============================================================================
+ # Windows Gateway (GTW) 内网 IP 地址 (示例配置)
+ # 用户需根据实际网络拓扑修改此值
+ MT5_HOST=192.168.x.x
+
+ # ZeroMQ REQ-REP 通信端口 (必须与 MT5 EA 配置一致)
+ MT5_PORT=5555
```

### .env.example 保持现状

已有的 Docker/ZeroMQ 配置无需修改，保持兼容性。

---

## 🔐 安全检查

- ✅ 无敏感信息泄露（客户端密钥、证书等）
- ✅ 内网通信（TCP 127.0.0.1/内网 IP），无需 TLS
- ✅ 代码仅建立连接，不修改生产数据
- ✅ 超时保护防止 Zombie 连接
- ⚠️ 生产部署建议：
  - 添加消息签名验证
  - 启用 ZeroMQ 认证机制
  - 限制客户端 IP 白名单

---

## 📊 性能与网络影响

- **CPU 使用**: 极低（等待 I/O）
- **内存使用**: < 50MB
- **网络**: 仅单条 TCP 连接，流量最小
- **延迟**: RTT < 100ms (局域网预期)

---

## 🔄 故障处理

### 如果 GTW 节点离线
```bash
# INF 节点会超时退出（5 秒超时）
# 日志中显示："[✗] Connection timeout"
# 无需中断，等待 GTW 恢复后重试
```

### 如果防火墙规则缺失
```bash
# GTW 节点 Windows 端：
# Control Panel > Windows Defender Firewall > Advanced Settings
# 入站规则 > 新建规则 > 端口 5555 TCP

# 或使用 PowerShell：
# New-NetFirewallRule -DisplayName "MT5 ZMQ" -Direction Inbound `
#   -LocalPort 5555 -Protocol TCP -Action Allow
```

---

## 📋 部署检查清单

在执行 double-gate 审查前，确认：

- [ ] pyzmq 已在所有 Linux 节点安装
- [ ] .env 中的 MT5_HOST 已更新为实际 GTW IP（或待用户更新）
- [ ] src/client/mt5_connector.py 已同步到所有节点
- [ ] scripts/audit_current_task.py 已更新
- [ ] 防火墙规则已在 GTW 上配置
- [ ] MT5 Server 已在 GTW 上运行
- [ ] 网络连通性已验证（ping 测试）

---

**同步优先级**: 🔴 关键（阻塞后续任务）
**预计同步时间**: < 10 分钟（包括依赖安装）
**回滚难度**: 🟢 低（仅新增，无破坏性修改）
