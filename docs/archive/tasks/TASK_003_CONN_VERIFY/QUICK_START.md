# TASK #003 快速启动指南

## 🚀 MT5 ZeroMQ 连接测试

### 前置条件
- Python 3.9+ 已安装
- pyzmq 已安装: `pip install pyzmq`
- Windows GTW 节点已运行 MT5 Server (端口 5555)
- Linux HUB 与 Windows GTW 网络互通

### 第一步：配置网络地址

编辑 `.env` 文件，修改 Windows GTW 的实际内网 IP：

```bash
# 打开 .env
nano .env

# 找到 MT5 ZeroMQ 配置段，修改为实际 IP
MT5_HOST=192.168.x.x     # <- 改为实际 Windows IP
MT5_PORT=5555             # 通常无需修改
```

查看现有配置:
```bash
grep -A2 "MT5 ZeroMQ" .env
```

### 第二步：运行连接测试

```bash
# 直接运行
python3 src/client/mt5_connector.py

# 或保存日志
python3 src/client/mt5_connector.py | tee VERIFY_LOG.log
```

### 预期成功输出

```
============================================================
MT5-CRS Python ZeroMQ Client Test
============================================================

[Config]
  MT5_HOST: 192.168.x.x
  MT5_PORT: 5555

[*] Connecting to MT5 Server at tcp://192.168.x.x:5555...
[✓] Connected to tcp://192.168.x.x:5555
[*] Sending test message 'Hello'...
[✓] Received reply: OK_FROM_MT5
[✓] Round-trip time: 45.23ms
[✓] Connection test PASSED

============================================================
```

### 常见问题排查

#### 问题 1：Connection timeout
```
[✗] Connection timeout - no response from MT5 Server
```

**排查步骤**:
1. 检查 MT5_HOST 是否正确：`grep MT5_HOST .env`
2. 测试网络连接：`ping 192.168.x.x`
3. 检查防火墙：GTW 上是否开放了 5555 端口
4. 确认 MT5 Server 已启动

#### 问题 2：Connection refused
```
[✗] Failed to connect: [Errno 111] Connection refused
```

**解决方案**:
- GTW 节点端口未开放
- MT5 Server 未运行
- IP 地址错误

#### 问题 3：ModuleNotFoundError: No module named 'zmq'
```
ModuleNotFoundError: No module named 'zmq'
```

**解决方案**:
```bash
pip install pyzmq
# 或
pip3 install pyzmq
```

---

## 高级用法

### 使用 Context Manager

```python
from src.client.mt5_connector import MT5Client

with MT5Client(host='192.168.x.x', port=5555) as client:
    if client.test_connection():
        print("✓ Connection successful")
    else:
        print("✗ Connection failed")
# 自动清理资源
```

### 自定义超时

```python
client = MT5Client(
    host='192.168.x.x',
    port=5555,
    timeout=10000  # 10 秒超时
)
```

### 环境变量配置

脚本自动从 `.env` 读取配置，无需手动传参：

```bash
# .env
MT5_HOST=192.168.100.50
MT5_PORT=5555

# 运行脚本时自动使用上述配置
python3 src/client/mt5_connector.py
```

---

## 验证框架测试

运行审计脚本验证连接框架是否完整：

```bash
# Gate 1 本地审计
python3 scripts/audit_current_task.py

# 预期输出
# 🔍 AUDIT: Task #003 MT5-ZEROMQ CONNECTION
# [✓] mt5_connector_class
# [✓] verify_log
# ...
```

---

## 故障日志分析

查看最近的连接日志：

```bash
# 查看日志文件
cat docs/archive/tasks/TASK_003_CONN_VERIFY/VERIFY_LOG.log

# 或实时查看
tail -f docs/archive/tasks/TASK_003_CONN_VERIFY/VERIFY_LOG.log
```

关键日志标签:
- `[✓]` - 成功
- `[✗]` - 失败
- `[*]` - 进行中
- `[!]` - 警告

---

## 网络拓扑图示

```
HUB (Linux)                      GTW (Windows)
  │                                │
  │ python3 src/client/           │
  │ mt5_connector.py              │
  │                                │
  │ MT5Client                      │
  │   │                            │
  │   ├─► ZeroMQ Context          │
  │   ├─► REQ Socket              │
  │   └─► connect()               │
  │        │                       │
  │        └─── TCP:5555 ────────►│ Listen 5555
  │             (ZeroMQ)          │
  │                               │ MT5 Server
  │  REP Socket ◄──────────────── │ EA
  │        │                      │
  │        └─ "OK_FROM_MT5"      │
  │                               │
  └───────────────────────────────┘
      内网通信 (内部 VPC)
      RTT < 100ms
```

---

## 性能指标

运行后检查延迟指标：

```bash
# 提取 RTT
grep "Round-trip time" VERIFY_LOG.log

# 输出示例
# [✓] Round-trip time: 45.23ms
```

**目标指标**:
- RTT < 100ms ✅ (局域网标准)
- 连接成功率 > 99% (冗余部署)

---

**就绪状态**: 使用本指南完成配置后，系统即可进入双重门禁审查
