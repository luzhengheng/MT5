# TASK #023 快速启动指南

## 🚀 基础设施整合与Timer Mode验证（周末准备）

### 前置条件
- Python 3.9+ 已安装
- pyzmq 已安装: `pip install pyzmq`
- 可以 ping 到 Windows GTW: 172.19.141.255
- Windows MT5 EA 已启用 Timer Mode
- 网络拓扑确认：HUB ↔ GTW 互通

### 📌 Timer Mode说明

Timer Mode 是 MT5 EA 的周末交易准备模式。该模式通过接收特定的激活信号（`Wake up Neo...`）来启动。

**消息流程**:
1. Linux 发送: `b"Wake up Neo..."`
2. MT5 EA 接收并进入 Timer Mode
3. MT5 回复: `OK_FROM_MT5`
4. 系统进入周末交易就绪状态

### 第一步：验证网络连接

```bash
# 测试与 GTW 的连接
ping -c 1 172.19.141.255

# 预期输出: 正常 ICMP 回应 (RTT < 100ms)
```

### 第二步：运行整合验证脚本

```bash
# 直接运行脚本
python3 scripts/verify_fix_v23.py

# 或保存日志
python3 scripts/verify_fix_v23.py | tee verify_task_023.log
```

### 预期成功输出

```
╔════════════════════════════════════════════╗
║     MT5-CRS TASK #023 INFRASTRUCTURE FIX   ║
║        Archive Consolidation & Verify      ║
╚════════════════════════════════════════════╝

======================================================================
[Cleanup] Starting archive cleanup process...
======================================================================

[✓] Deleted: docs/archive/tasks/TASK_003_CONN_VERIFY
[✓] Deleted: docs/archive/tasks/TASK_004_CONN_TEST

[Cleanup]: Summary
  - docs/archive/tasks/TASK_003_CONN_VERIFY: SUCCESS
  - docs/archive/tasks/TASK_004_CONN_TEST: SUCCESS

======================================================================
[Network] Measuring ping latency...
======================================================================

[✓] Ping result: 64 bytes from 172.19.141.255: ... time=0.495 ms

======================================================================
[Connection] Verifying MT5 Server connectivity...
======================================================================

[✓] Connected to tcp://172.19.141.255:5555
[✓] Received: OK_FROM_MT5
[✓] RTT: 45.23ms

[Connection]: ESTABLISHED
[Verification]: COMPLETE

[Status] Ready for production deployment
```

---

## 故障排查

### 问题 1: 档案仍然存在

```
[!] Path already missing: docs/archive/tasks/TASK_003_CONN_VERIFY
```

**解决方案**:
- 这是预期行为（档案已被清理）
- 脚本会标记为成功

### 问题 2: Ping 失败

```
ping: 172.19.141.255: Temporary failure in name resolution
```

**排查步骤**:
1. **检查网络**: `ip route` 或 `route -n`
2. **检查连通性**: `traceroute 172.19.141.255`
3. **检查防火墙**: `sudo iptables -L -n | grep 172.19`

### 问题 3: ZeroMQ 连接超时

```
[!] Connection timeout (expected if MT5 Server offline)
[Connection]: TIMEOUT (Server may be offline)
```

**排查步骤**:
1. 确认 Windows GTW MT5 Server 已启动
2. 检查防火墙: `netstat -an | grep 5555` (Windows)
3. 验证服务状态: `ps aux | grep mt5` (Linux)

### 问题 4: ModuleNotFoundError: No module named 'zmq'

```bash
pip install --upgrade pyzmq
python3 -c "import zmq; print(zmq.__version__)"
```

---

## 手动清理（如果脚本失败）

```bash
# 手动删除档案目录
rm -rf docs/archive/tasks/TASK_003_CONN_VERIFY
rm -rf docs/archive/tasks/TASK_004_CONN_TEST

# 验证删除
ls -la docs/archive/tasks/ | grep TASK_00[34]
# 应该返回空结果
```

---

## 验证框架测试

运行审计脚本验证整合是否完整：

```bash
# Gate 1 本地审计
python3 scripts/audit_current_task.py

# 预期输出 (成功时)
# 🔍 AUDIT: Task #023 INFRASTRUCTURE CONSOLIDATION
# [✓] scripts/verify_fix_v23.py exists with cleanup logic
# [✓] docs/.../VERIFY_LOG.log exists
# [✓] Connection established indicator found
# [✓] Archive cleanup verified
# ...
# 📊 Audit Summary: 7/7 checks passed
```

---

## 监控脚本健康状态

```bash
# 查看最近的执行日志
tail -50 docs/archive/tasks/TASK_023_INFRA_FIX/VERIFY_LOG.log

# 检查档案清理状态
ls -la docs/archive/tasks/ | grep -E "TASK_00[34]"
# 应该返回空结果

# 验证新档案目录
ls -la docs/archive/tasks/TASK_023_INFRA_FIX/
```

---

## 性能指标

执行后查看网络指标：

```bash
# 提取 Ping 延迟
grep "time=" docs/archive/tasks/TASK_023_INFRA_FIX/VERIFY_LOG.log

# 提取 ZeroMQ RTT
grep "RTT:" docs/archive/tasks/TASK_023_INFRA_FIX/VERIFY_LOG.log

# 输出示例
# [✓] Ping result: ... time=0.495 ms
# [✓] RTT: 45.23ms
```

**目标指标**:
- Ping RTT < 10ms ✅ (内网标准)
- ZeroMQ RTT < 100ms ✅ (应用阈值)
- 清理成功率 100% ✅

---

## 生产部署检查清单

在进行双重门禁审查前，确认：

- [ ] Windows GTW 已运行 MT5 Server (172.19.141.255:5555)
- [ ] 防火墙规则已开放端口 5555 TCP
- [ ] pyzmq 已在 Linux 节点安装
- [ ] 网络连通性已验证 (ping < 10ms)
- [ ] 脚本已执行并生成 VERIFY_LOG.log
- [ ] 日志包含 `[Cleanup]: Deleted TASK_003/004`
- [ ] 日志包含 `[Connection]: ESTABLISHED`
- [ ] 本地审计 (`audit_current_task.py`) 已通过
- [ ] TASK_003/004 目录已从文件系统删除

---

**部署状态**: 使用本指南完成验证后，系统即可进入双重门禁审查阶段

