# Task #106 - MT5 Live Bridge 快速启动指南

## 5 分钟快速启动

本指南将帮助你在 **5 分钟内** 启动 MT5 Live Bridge，实现 Linux 推理节点到 Windows 交易网关的实盘连接。

---

## 前置条件检查

### Linux Inf 节点要求

- ✅ Python 3.9+
- ✅ 网络连通性：可访问 Windows GTW 节点（IP: `172.19.141.249`）
- ✅ 端口开放：可连接到 GTW 的 `5555` 端口

### Windows GTW 节点要求

- ✅ Python 3.9+
- ✅ MT5 终端已安装并登录（真实账户或 Demo 账户）
- ✅ 防火墙开放：入站规则允许 `5555` 端口

---

## 第一步：Windows GTW 端启动（2 分钟）

### 1.1 安装依赖

在 Windows GTW 节点打开 **PowerShell** 或 **CMD**：

```powershell
# 切换到项目目录
cd C:\mt5-crs

# 安装必要的 Python 包
pip install pyzmq MetaTrader5 pyyaml
```

**验证安装**:
```powershell
python -c "import zmq; import MetaTrader5 as mt5; print('Dependencies OK')"
```

### 1.2 配置 MT5 连接

编辑配置文件 `config/mt5_connection.yaml`（如果不存在则创建）：

```yaml
# MT5 连接配置
mt5:
  # MT5 登录信息
  login: 12345678          # 替换为你的 MT5 账号
  password: "your_password"  # 替换为你的 MT5 密码
  server: "Broker-Server"   # 替换为你的经纪商服务器

  # MT5 终端路径（可选，自动检测）
  terminal_path: "C:\\Program Files\\MetaTrader 5\\terminal64.exe"

# ZMQ 服务器配置
zmq_server:
  port: 5555
  bind_address: "*"  # 监听所有网络接口
  timeout_ms: 5000   # 5 秒超时

# 安全配置
security:
  # IP 白名单（仅允许来自这些 IP 的连接）
  allowed_ips:
    - "172.19.141.250"  # Linux Inf 节点 IP
    - "127.0.0.1"       # 本地测试

  # Risk Signature 验证
  signature_expiry_seconds: 2  # 签名有效期 2 秒
  require_signature: true      # 强制要求签名
```

### 1.3 启动 MT5 ZMQ Server

```powershell
# 启动服务器（前台运行）
python scripts\gateway\mt5_zmq_server.py

# 或使用后台运行（生产环境）
start /B python scripts\gateway\mt5_zmq_server.py > logs\mt5_zmq_server.log 2>&1
```

**预期输出**:
```
[2026-01-15 10:00:00,000] [INFO] MT5 ZMQ Server starting...
[2026-01-15 10:00:00,123] [INFO] MT5 initialized successfully
[2026-01-15 10:00:00,234] [INFO] Account: 12345678, Balance: 100000.00 USD
[2026-01-15 10:00:00,345] [INFO] ZMQ REP socket bound to tcp://*:5555
[2026-01-15 10:00:00,456] [INFO] Server ready, waiting for requests...
```

**故障排查**:
- ❌ `MT5 initialization failed` → 检查 MT5 终端是否已登录
- ❌ `Address already in use` → 端口 5555 被占用，关闭其他程序或更换端口
- ❌ `ImportError: No module named 'MetaTrader5'` → 重新安装 `pip install MetaTrader5`

---

## 第二步：Linux Inf 端启动（2 分钟）

### 2.1 安装依赖

在 Linux Inf 节点：

```bash
# 切换到项目目录
cd /opt/mt5-crs

# 激活虚拟环境（如果使用）
source venv/bin/activate

# 安装必要的 Python 包
pip3 install pyzmq pyyaml
```

**验证安装**:
```bash
python3 -c "import zmq; import yaml; print('Dependencies OK')"
```

### 2.2 配置连接参数

编辑 `config/mt5_connection.yaml`:

```yaml
# Linux Inf 端配置
mt5_client:
  # Windows GTW 节点地址
  gtw_address: "tcp://172.19.141.249:5555"

  # 连接超时
  timeout_ms: 5000  # 5 秒

  # 重试策略
  retry_attempts: 3
  retry_delay_ms: 1000  # 1 秒

# 心跳监控
heartbeat:
  interval_seconds: 5      # 每 5 秒 PING 一次
  failure_threshold: 3     # 连续失败 3 次触发熔断
  auto_restart: true       # 自动重启心跳监控

# 风险监控（Task #105 集成）
risk_monitor:
  enabled: true
  config_path: "config/risk_config.yaml"
```

### 2.3 快速测试连接

使用内置的测试脚本验证连接：

```bash
# 测试 PING（心跳探测）
python3 -c "
from src.gateway.mt5_client import MT5Client
client = MT5Client(server_address='tcp://172.19.141.249:5555')
response = client.ping()
print(f'PING Response: {response}')
"
```

**预期输出**:
```json
PING Response: {
  "status": "ok",
  "server_time": "2026-01-15T10:05:00.123456Z",
  "latency_ms": 2.345
}
```

### 2.4 启动 MT5 Live Connector

```bash
# 方式 1: 交互式启动（测试环境）
python3 src/execution/mt5_live_connector.py --mode=interactive

# 方式 2: 后台启动（生产环境）
nohup python3 src/execution/mt5_live_connector.py --mode=production > logs/mt5_live_connector.log 2>&1 &

# 检查进程状态
ps aux | grep mt5_live_connector
```

**预期输出**:
```
[2026-01-15 10:10:00,000] [INFO] MT5LiveConnector initializing...
[2026-01-15 10:10:00,123] [INFO] RiskMonitor loaded successfully
[2026-01-15 10:10:00,234] [INFO] CircuitBreaker loaded successfully
[2026-01-15 10:10:00,345] [INFO] HeartbeatMonitor started (interval: 5s)
[2026-01-15 10:10:00,456] [INFO] MT5Client connected to tcp://172.19.141.249:5555
[2026-01-15 10:10:05,567] [INFO] Heartbeat OK - Latency: 2.34ms
[2026-01-15 10:10:10,678] [INFO] Heartbeat OK - Latency: 2.56ms
```

---

## 第三步：发送测试订单（1 分钟）

### 3.1 测试 PING（心跳探测）

```python
from src.execution.mt5_live_connector import MT5LiveConnector

# 创建连接器实例
connector = MT5LiveConnector(
    gtw_address="tcp://172.19.141.249:5555",
    risk_config_path="config/risk_config.yaml"
)

# 测试心跳
response = connector.ping()
print(f"PING Latency: {response['latency_ms']:.2f}ms")
```

**预期输出**:
```
PING Latency: 2.34ms
```

### 3.2 测试 OPEN（开仓订单）

**重要**: 以下示例使用 **0.01 手**（最小手数），亏损风险极低。

```python
from src.execution.mt5_live_connector import MT5LiveConnector

connector = MT5LiveConnector(
    gtw_address="tcp://172.19.141.249:5555",
    risk_config_path="config/risk_config.yaml"
)

# 构造订单（0.01 手 EURUSD）
order = {
    "symbol": "EURUSD",
    "type": "BUY",
    "volume": 0.01,       # 最小手数
    "price": 0.0,         # 市价单
    "sl": 1.05000,        # 止损价
    "tp": 1.06000,        # 止盈价
    "comment": "TEST_ORDER_TASK_106"
}

# 发送订单（自动附加 Risk Signature）
try:
    response = connector.open_order(order)
    print(f"Order Status: {response['status']}")
    print(f"Ticket: {response['ticket']}")
    print(f"Fill Price: {response['price']}")
    print(f"Latency: {response['latency_ms']:.2f}ms")
except Exception as e:
    print(f"Order Failed: {e}")
```

**成功输出示例**:
```
Order Status: FILLED
Ticket: 12345678
Fill Price: 1.05230
Latency: 45.67ms
```

**拒绝示例（无 Risk Signature）**:
```
Order Failed: REJECTED - MISSING_SIGNATURE
```

### 3.3 测试 CLOSE（平仓订单）

```python
# 平掉刚才开的订单
response = connector.close_order(
    ticket=12345678,
    symbol="EURUSD",
    volume=0.01
)
print(f"Close Status: {response['status']}")
print(f"Close Price: {response['price']}")
```

### 3.4 测试 GET_ACCOUNT（账户查询）

```python
# 查询账户余额
account = connector.get_account()
print(f"Balance: ${account['balance']:.2f}")
print(f"Equity: ${account['equity']:.2f}")
print(f"Margin Level: {account['margin_level']:.2f}%")
```

**预期输出**:
```
Balance: $100000.00
Equity: $100005.00
Margin Level: 20100.10%
```

---

## 常见问题排查

### Q1: 连接超时 `zmq.error.Again`

**现象**:
```
zmq.error.Again: Resource temporarily unavailable
```

**原因**:
- Windows GTW 服务器未启动
- 防火墙阻止 5555 端口
- 网络不通（无法 ping 通 GTW IP）

**解决方案**:
```bash
# 1. 检查 GTW 服务器是否运行
# 在 Windows GTW 上执行：
netstat -an | findstr 5555

# 2. 检查网络连通性
# 在 Linux Inf 上执行：
ping 172.19.141.249
telnet 172.19.141.249 5555

# 3. 检查防火墙（Windows GTW）
# 打开 PowerShell（管理员）：
New-NetFirewallRule -DisplayName "MT5 ZMQ Port 5555" `
    -Direction Inbound -Protocol TCP -LocalPort 5555 -Action Allow
```

---

### Q2: 订单被拒绝 `MISSING_SIGNATURE`

**现象**:
```json
{
  "status": "REJECTED",
  "error_code": "MISSING_SIGNATURE",
  "error_msg": "risk_signature field is required"
}
```

**原因**:
订单未通过 RiskMonitor 验证，缺少 `risk_signature` 字段。

**解决方案**:
确保使用 `MT5LiveConnector.open_order()` 方法，而不是直接调用 `MT5Client`：

```python
# ❌ 错误方式（绕过 RiskMonitor）
from src.gateway.mt5_client import MT5Client
client = MT5Client(server_address='tcp://172.19.141.249:5555')
client.send_order({"symbol": "EURUSD", "type": "BUY", "volume": 0.01})

# ✅ 正确方式（自动附加 Risk Signature）
from src.execution.mt5_live_connector import MT5LiveConnector
connector = MT5LiveConnector(gtw_address='tcp://172.19.141.249:5555')
connector.open_order({"symbol": "EURUSD", "type": "BUY", "volume": 0.01})
```

---

### Q3: 心跳失败触发熔断

**现象**:
```
[CRITICAL] HEARTBEAT FAILURE - Engaging Circuit Breaker
[ERROR] CircuitBreaker engaged: HEARTBEAT_FAILURE
```

**原因**:
连续 3 次 PING 失败（15 秒内无响应）。

**解决方案**:
```bash
# 1. 检查 GTW 服务器是否运行
# 在 Windows GTW 上：
tasklist | findstr python

# 2. 重启 GTW 服务器
python scripts\gateway\mt5_zmq_server.py

# 3. 重启 HeartbeatMonitor（Linux Inf）
# 熔断器会自动重置，无需手动操作
```

---

### Q4: MT5 初始化失败

**现象**（Windows GTW）:
```
[ERROR] MT5 initialization failed: NOT_AVAILABLE
```

**原因**:
- MT5 终端未启动
- MT5 终端未登录账户
- MetaTrader5 Python 包与 MT5 版本不兼容

**解决方案**:
```powershell
# 1. 打开 MT5 终端并登录账户（真实账户或 Demo）
# 手动启动 MT5 并确保已登录

# 2. 验证 MT5 API 可用性
python -c "import MetaTrader5 as mt5; print(mt5.initialize())"

# 3. 检查 MT5 版本
# MT5 终端 > 帮助 > 关于 > 版本号（需 >= 5.0.37）

# 4. 重新安装 MetaTrader5 包
pip uninstall MetaTrader5
pip install MetaTrader5 --upgrade
```

---

### Q5: 订单被 MT5 拒绝 `INVALID_VOLUME`

**现象**:
```json
{
  "status": "REJECTED",
  "error_code": "INVALID_VOLUME",
  "error_msg": "Invalid lot size"
}
```

**原因**:
- 手数 `volume` 不符合经纪商要求（如最小 0.01 手，步进 0.01 手）
- 账户保证金不足

**解决方案**:
```python
# 1. 查询品种信息
from src.gateway.mt5_client import MT5Client
client = MT5Client(server_address='tcp://172.19.141.249:5555')
symbol_info = client.get_symbol_info("EURUSD")
print(f"Min Volume: {symbol_info['volume_min']}")
print(f"Max Volume: {symbol_info['volume_max']}")
print(f"Volume Step: {symbol_info['volume_step']}")

# 2. 调整手数
order = {
    "symbol": "EURUSD",
    "type": "BUY",
    "volume": 0.01,  # 使用最小手数
    ...
}
```

---

## 生产环境部署建议

### 1. 环境变量配置

为避免硬编码敏感信息，使用环境变量：

**Linux Inf (`~/.bashrc`)**:
```bash
export MT5_GTW_ADDRESS="tcp://172.19.141.249:5555"
export MT5_RISK_CONFIG="/opt/mt5-crs/config/risk_config.yaml"
export MT5_LOG_LEVEL="INFO"
```

**Windows GTW (`设置 > 系统 > 高级系统设置 > 环境变量`)**:
```
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_SERVER=Broker-Server
MT5_ZMQ_PORT=5555
```

### 2. 日志管理

```bash
# Linux Inf
mkdir -p /var/log/mt5_crs
ln -s /opt/mt5-crs/logs/mt5_live_connector.log /var/log/mt5_crs/

# Windows GTW
mkdir C:\mt5_crs\logs
# 日志自动写入 C:\mt5_crs\logs\mt5_zmq_server.log
```

### 3. 进程守护

**Linux Inf (使用 systemd)**:

创建 `/etc/systemd/system/mt5-live-connector.service`:
```ini
[Unit]
Description=MT5 Live Connector Service
After=network.target

[Service]
Type=simple
User=mt5user
WorkingDirectory=/opt/mt5-crs
ExecStart=/usr/bin/python3 src/execution/mt5_live_connector.py --mode=production
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mt5-live-connector
sudo systemctl start mt5-live-connector
sudo systemctl status mt5-live-connector
```

**Windows GTW (使用 NSSM)**:

```powershell
# 下载 NSSM: https://nssm.cc/download
nssm install MT5ZmqServer "C:\Python39\python.exe" "C:\mt5-crs\scripts\gateway\mt5_zmq_server.py"
nssm set MT5ZmqServer AppDirectory "C:\mt5-crs"
nssm set MT5ZmqServer AppStdout "C:\mt5-crs\logs\mt5_zmq_server.log"
nssm set MT5ZmqServer AppStderr "C:\mt5-crs\logs\mt5_zmq_server_error.log"
nssm start MT5ZmqServer
```

### 4. 监控告警

**心跳监控告警**（Linux Inf）:

```bash
# 监控日志中的 HEARTBEAT FAILURE
tail -f /var/log/mt5_crs/mt5_live_connector.log | grep --line-buffered "HEARTBEAT FAILURE" | while read line; do
    echo "$line" | mail -s "[ALERT] MT5 Heartbeat Failure" admin@example.com
done
```

---

## 性能基准测试

### 延迟测试脚本

```python
import time
import statistics
from src.execution.mt5_live_connector import MT5LiveConnector

connector = MT5LiveConnector(gtw_address="tcp://172.19.141.249:5555")

# 测试 100 次 PING
latencies = []
for _ in range(100):
    start = time.time()
    response = connector.ping()
    latency = (time.time() - start) * 1000  # 转换为毫秒
    latencies.append(latency)
    time.sleep(0.1)

# 统计结果
print(f"Mean Latency: {statistics.mean(latencies):.2f}ms")
print(f"P50 Latency: {statistics.median(latencies):.2f}ms")
print(f"P95 Latency: {statistics.quantiles(latencies, n=20)[18]:.2f}ms")
print(f"P99 Latency: {statistics.quantiles(latencies, n=100)[98]:.2f}ms")
print(f"Max Latency: {max(latencies):.2f}ms")
```

**目标性能指标**:
- P50: < 5ms
- P95: < 10ms
- P99: < 20ms

---

## 下一步

完成快速启动后，建议继续：

1. **阅读完整架构文档** - [ARCHITECTURE.md](ARCHITECTURE.md)
2. **学习部署同步流程** - [SYNC_GUIDE.md](SYNC_GUIDE.md)
3. **查看完成报告** - [COMPLETION_REPORT.md](COMPLETION_REPORT.md)
4. **集成到策略引擎** - 参考 `src/strategy/` 示例代码

---

## 技术支持

如遇到未在本文档中列出的问题：

1. **查看日志**:
   - Linux: `/var/log/mt5_crs/mt5_live_connector.log`
   - Windows: `C:\mt5-crs\logs\mt5_zmq_server.log`

2. **运行审计脚本**:
   ```bash
   python3 /opt/mt5-crs/scripts/audit_task_106.py
   ```

3. **查看验证日志**:
   ```bash
   cat /opt/mt5-crs/VERIFY_LOG.log | tail -100
   ```

4. **联系开发团队**:
   - GitHub Issues: [项目仓库 Issues 页面]
   - 邮件: support@mt5-crs.example.com

---

**文档版本**: v1.0
**最后更新**: 2026-01-15
**Protocol**: v4.3 (Zero-Trust Edition)
**作者**: Claude Sonnet 4.5 (MT5-CRS Hub Agent)

---

**END OF QUICK START GUIDE**
