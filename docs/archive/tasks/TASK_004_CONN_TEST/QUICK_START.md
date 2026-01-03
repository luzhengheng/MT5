# TASK #004 快速启动指南

## 🚀 MT5 Live Connection Test

### 前置条件
- Python 3.9+ 已安装
- pyzmq 已安装: `pip install pyzmq`
- Windows GTW 节点正在运行 MT5 Server (端口 5555)
- Linux HUB 与 Windows GTW 网络互通（172.19.141.255 可达）

### 第一步：确认网络连通性

```bash
# 测试与 GTW 的网络连接
ping 172.19.141.255

# 预期输出: 正常 ICMP 回应 (RTT < 100ms)
```

### 第二步：运行连接验证

```bash
# 直接运行脚本
python3 scripts/verify_connection.py

# 或保存日志
python3 scripts/verify_connection.py | tee test_output.log
```

### 预期成功输出

```
============================================================
MT5-CRS Live Connection Verification (Task #004)
============================================================

[Config]
  MT5_HOST: 172.19.141.255
  MT5_PORT: 5555
  Timeout: 5000ms

[*] Connecting to MT5 Server at tcp://172.19.141.255:5555...
[✓] Connected to tcp://172.19.141.255:5555

[*] Sending test message 'Hello'...
[*] Waiting for response (timeout: 5000ms)...
[✓] Received reply: OK_FROM_MT5
[✓] Round-trip time: 47.35ms

[✓] Connection test PASSED
    MT5 Server responded with correct handshake
```

### 常见问题排查

#### 问题 1: Connection timeout
```
[✗] Connection timeout - no response from MT5 Server
    Waited 5000ms without receiving response
```

**排查步骤**:
1. **验证网络**: `ping 172.19.141.255`
2. **检查 MT5 Server**: 确认 Windows GTW 上 MT5 EA 已启动
3. **检查端口**:
   ```bash
   # Windows GTW 上执行
   netstat -an | find "5555"
   # 或使用 PowerShell
   Get-NetTCPConnection -LocalPort 5555
   ```
4. **检查防火墙**:
   ```
   Control Panel > Windows Defender Firewall > Advanced Settings
   入站规则 > 新建规则 > 端口 5555 TCP > 允许
   ```

#### 问题 2: Connection refused
```
[✗] Connection refused: [Errno 111] Connection refused
```

**解决方案**:
- MT5 Server 未运行 - 在 GTW 上启动 MetaTrader 5 和 EA
- 端口未开放 - 检查 Windows 防火墙设置
- IP 地址错误 - 确认 GTW 的正确内网 IP 是 172.19.141.255

#### 问题 3: ModuleNotFoundError: No module named 'zmq'
```
ModuleNotFoundError: No module named 'zmq'
```

**解决方案**:
```bash
pip install pyzmq
# 或
pip3 install pyzmq

# 验证安装
python3 -c "import zmq; print(zmq.__version__)"
```

#### 问题 4: Unexpected response
```
[✘] Unexpected response: 'SOME_OTHER_MESSAGE'
    Expected: 'OK_FROM_MT5'
```

**排查步骤**:
1. 确认 MT5 EA 代码返回正确的握手字符串 "OK_FROM_MT5"
2. 检查网络传输是否产生了消息损坏
3. 验证 ZeroMQ 消息编码格式（UTF-8）

---

## 高级用法

### 使用脚本的 Python 导入

虽然脚本通常独立运行，但可以集成到其他工具：

```python
import sys
sys.path.insert(0, '/opt/mt5-crs/scripts')

# 方式 1: 直接运行脚本
import subprocess
result = subprocess.run(['python3', 'scripts/verify_connection.py'],
                       capture_output=True, text=True)
print(result.stdout)

# 方式 2: 集成到监控系统
if "OK_FROM_MT5" in result.stdout:
    print("✓ MT5 Connection Healthy")
else:
    print("✗ MT5 Connection Failed")
```

### 修改目标地址（仅用于测试）

脚本中的目标地址已硬编码为 `172.19.141.255:5555`（TASK #004 要求）。
如需测试不同地址，可临时修改脚本：

```python
# scripts/verify_connection.py 中
MT5_HOST = "172.19.141.255"  # 修改此处（仅用于调试）
MT5_PORT = 5555
```

**注意**: 生产部署中必须恢复硬编码值。

### 自定义超时设置

```python
# 若需更长超时（例如 WAN 延迟）
TIMEOUT_MS = 10000  # 10 秒
```

---

## 网络诊断工具

### Windows GTW 端诊断

```powershell
# 检查 MT5 是否在监听
netstat -an | findstr "5555"
# 或
Get-NetTCPConnection -LocalPort 5555 -ErrorAction SilentlyContinue

# 检查防火墙规则
Get-NetFirewallRule -DisplayName "*MT5*" -ErrorAction SilentlyContinue

# 测试端口开放
Test-NetConnection -ComputerName 172.19.141.254 -Port 5555
```

### Linux HUB 端诊断

```bash
# 测试网络连接
ping 172.19.141.255

# 使用 nc（netcat）测试端口
nc -zv 172.19.141.255 5555

# 使用 telnet
telnet 172.19.141.255 5555

# 检查本地 ZeroMQ 状态
python3 -c "import zmq; print(f'ZeroMQ: {zmq.zmq_version()}')"
```

---

## 验证框架测试

运行审计脚本验证连接框架是否完整：

```bash
# Gate 1 本地审计
python3 scripts/audit_current_task.py

# 预期输出 (成功时)
# 🔍 AUDIT: Task #004 LIVE MT5 CONNECTION TEST
# [✓] scripts/verify_connection.py exists with REQ mode and hardcoded IP
# [✓] docs/.../VERIFY_LOG.log exists
# [✓] Found 'Received reply: OK_FROM_MT5' in log - CONNECTION CONFIRMED
# ...
# 📊 Audit Summary: 6/6 checks passed
```

---

## 性能指标

执行后查看连接性能：

```bash
# 提取 RTT
grep "Round-trip time" docs/archive/tasks/TASK_004_CONN_TEST/VERIFY_LOG.log

# 输出示例
# [✓] Round-trip time: 47.35ms
```

**目标指标**:
- RTT < 100ms ✅ (局域网标准)
- 连接成功率 > 99% ✅ (内网可靠性)
- 响应时间稳定 ✅ (< 50ms 波动)

---

## 生产部署检查清单

在部署到生产环境前，确认以下项目：

- [ ] MT5 Server 已在 Windows GTW (172.19.141.255) 上运行
- [ ] EA 脚本正确返回 "OK_FROM_MT5" 握手字符串
- [ ] 防火墙规则已配置允许端口 5555 TCP
- [ ] 网络拓扑已验证 (HUB ↔ GTW 互通)
- [ ] 本地审计 (`audit_current_task.py`) 已通过
- [ ] 外部审计 (`gemini_review_bridge.py`) 已通过
- [ ] RTT 延迟 < 100ms 已确认

---

**部署状态**: 使用本指南完成配置后，系统即可进入生产验证阶段

