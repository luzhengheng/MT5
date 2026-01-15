# Task #106 - MT5 Live Bridge 部署同步指南

## 部署架构概览

本指南提供完整的部署同步流程，确保 Linux Inf 节点和 Windows GTW 节点的配置一致性。

```
┌─────────────────────────────────────────────────────────────────┐
│ 部署拓扑                                                         │
│                                                                  │
│  ┌──────────────────┐         ZMQ Port 5555        ┌──────────┐│
│  │  Linux Inf Node  │◄──────────────────────────────┤ Windows  ││
│  │  172.19.141.250  │                                │ GTW Node ││
│  │                  │──────────────────────────────►│ 172.19.  ││
│  │  - mt5_live_     │    REQ/REP + PUB/SUB          │ 141.249  ││
│  │    connector.py  │    (Encrypted Optional)       │          ││
│  │  - heartbeat_    │                                │ - mt5_   ││
│  │    monitor.py    │                                │   zmq_   ││
│  │  - risk_monitor  │                                │   server ││
│  │                  │                                │ - MT5    ││
│  └──────────────────┘                                │   Term   ││
│                                                       └──────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## 第一阶段：环境准备

### 1.1 Linux Inf 节点配置

#### 1.1.1 系统要求

| 组件 | 要求 | 验证命令 |
|------|------|---------|
| 操作系统 | Linux (CentOS 7+, Ubuntu 18.04+) | `cat /etc/os-release` |
| Python 版本 | Python 3.9+ | `python3 --version` |
| 内存 | >= 4GB | `free -h` |
| 磁盘空间 | >= 10GB 可用 | `df -h /opt` |
| 网络 | 可访问 172.19.141.249:5555 | `telnet 172.19.141.249 5555` |

#### 1.1.2 环境变量配置

编辑 `~/.bashrc` 或 `/etc/environment`:

```bash
# MT5-CRS 项目路径
export MT5_CRS_ROOT="/opt/mt5-crs"
export MT5_CRS_CONFIG="/opt/mt5-crs/config"
export MT5_CRS_LOGS="/var/log/mt5_crs"

# MT5 GTW 连接信息
export MT5_GTW_ADDRESS="tcp://172.19.141.249:5555"
export MT5_GTW_TIMEOUT="5000"  # 5 秒超时

# 风险监控配置
export MT5_RISK_CONFIG="/opt/mt5-crs/config/risk_config.yaml"
export MT5_RISK_SIGNATURE_REQUIRED="true"

# 日志配置
export MT5_LOG_LEVEL="INFO"
export MT5_LOG_FILE="/var/log/mt5_crs/mt5_live_connector.log"

# Lock 文件目录（Task #104 CircuitBreaker 使用）
export MT5_CRS_LOCK_DIR="/var/lock/mt5_crs"

# Python 路径（确保能导入项目模块）
export PYTHONPATH="/opt/mt5-crs:$PYTHONPATH"
```

**应用环境变量**:
```bash
source ~/.bashrc
# 验证
echo $MT5_GTW_ADDRESS
```

#### 1.1.3 创建必要目录

```bash
# 创建日志目录
sudo mkdir -p /var/log/mt5_crs
sudo chown $USER:$USER /var/log/mt5_crs
sudo chmod 755 /var/log/mt5_crs

# 创建 Lock 文件目录（CircuitBreaker 熔断器使用）
sudo mkdir -p /var/lock/mt5_crs
sudo chown $USER:$USER /var/lock/mt5_crs
sudo chmod 755 /var/lock/mt5_crs

# 创建配置备份目录
mkdir -p $MT5_CRS_ROOT/config/backup

# 验证目录权限
ls -ld /var/log/mt5_crs /var/lock/mt5_crs
```

#### 1.1.4 依赖包安装

```bash
# 激活虚拟环境（推荐）
cd /opt/mt5-crs
python3 -m venv venv
source venv/bin/activate

# 安装核心依赖
pip3 install --upgrade pip
pip3 install pyzmq>=25.0.0
pip3 install pyyaml>=6.0
pip3 install python-dateutil>=2.8.0

# 安装开发依赖（可选，用于测试）
pip3 install pytest>=7.0.0
pip3 install pytest-cov>=4.0.0
pip3 install pylint>=2.15.0
pip3 install mypy>=1.0.0

# 验证安装
python3 -c "import zmq; import yaml; print('Core dependencies OK')"
```

**离线安装（无外网环境）**:
```bash
# 在有网络的机器上下载包
pip3 download -d /tmp/mt5_deps pyzmq pyyaml python-dateutil

# 传输到目标机器后安装
pip3 install --no-index --find-links=/tmp/mt5_deps pyzmq pyyaml python-dateutil
```

---

### 1.2 Windows GTW 节点配置

#### 1.2.1 系统要求

| 组件 | 要求 | 验证方法 |
|------|------|---------|
| 操作系统 | Windows 10+, Windows Server 2016+ | `winver` |
| Python 版本 | Python 3.9+ (64-bit) | `python --version` |
| 内存 | >= 8GB | 任务管理器 > 性能 |
| 磁盘空间 | >= 20GB 可用 | 磁盘管理 |
| MT5 终端 | MetaTrader 5 >= 5.0.37 | MT5 > 帮助 > 关于 |
| 网络 | 防火墙开放 5555 入站 | `netstat -an \| findstr 5555` |

#### 1.2.2 环境变量配置

**方式 1: 图形界面配置**
1. 右键 `此电脑` > `属性` > `高级系统设置` > `环境变量`
2. 在 `系统变量` 中点击 `新建`，依次添加：

| 变量名 | 变量值 |
|--------|--------|
| `MT5_CRS_ROOT` | `C:\mt5-crs` |
| `MT5_LOGIN` | `12345678`（你的 MT5 账号） |
| `MT5_PASSWORD` | `your_password`（你的 MT5 密码） |
| `MT5_SERVER` | `Broker-Server`（经纪商服务器） |
| `MT5_ZMQ_PORT` | `5555` |
| `MT5_ZMQ_BIND` | `*`（监听所有接口） |
| `MT5_LOG_FILE` | `C:\mt5-crs\logs\mt5_zmq_server.log` |
| `PYTHONPATH` | `C:\mt5-crs` |

**方式 2: PowerShell 配置**
```powershell
# 以管理员身份运行 PowerShell
[System.Environment]::SetEnvironmentVariable("MT5_CRS_ROOT", "C:\mt5-crs", "Machine")
[System.Environment]::SetEnvironmentVariable("MT5_ZMQ_PORT", "5555", "Machine")
[System.Environment]::SetEnvironmentVariable("PYTHONPATH", "C:\mt5-crs", "Machine")

# 验证
[System.Environment]::GetEnvironmentVariable("MT5_CRS_ROOT", "Machine")
```

#### 1.2.3 创建必要目录

```powershell
# 创建项目目录
New-Item -ItemType Directory -Path "C:\mt5-crs" -Force
New-Item -ItemType Directory -Path "C:\mt5-crs\logs" -Force
New-Item -ItemType Directory -Path "C:\mt5-crs\config" -Force
New-Item -ItemType Directory -Path "C:\mt5-crs\scripts\gateway" -Force
New-Item -ItemType Directory -Path "C:\mt5-crs\src\execution" -Force

# 验证目录结构
Get-ChildItem -Path "C:\mt5-crs" -Recurse -Directory
```

#### 1.2.4 依赖包安装

```powershell
# 检查 Python 版本
python --version  # 必须是 3.9+ 64-bit

# 升级 pip
python -m pip install --upgrade pip

# 安装核心依赖
pip install pyzmq>=25.0.0
pip install MetaTrader5>=5.0.4508
pip install pyyaml>=6.0
pip install python-dateutil>=2.8.0

# 验证 MT5 API 可用性
python -c "import MetaTrader5 as mt5; print('MT5 version:', mt5.version())"
```

**常见问题**:
- ❌ `ImportError: DLL load failed` → 安装 Visual C++ Redistributable (https://aka.ms/vs/17/release/vc_redist.x64.exe)
- ❌ `pip install MetaTrader5` 失败 → 使用离线安装：下载 `.whl` 文件手动安装

---

## 第二阶段：文件部署清单

### 2.1 Linux Inf 节点文件清单

需要从代码仓库同步的文件：

| 源路径（仓库） | 目标路径（Inf 节点） | 用途 | 必需 |
|---------------|---------------------|------|------|
| `src/execution/mt5_live_connector.py` | `/opt/mt5-crs/src/execution/` | 主连接器 | ✅ |
| `src/execution/heartbeat_monitor.py` | `/opt/mt5-crs/src/execution/` | 心跳监控 | ✅ |
| `src/execution/secure_loader.py` | `/opt/mt5-crs/src/execution/` | 安全加载器 | ✅ |
| `src/execution/risk_monitor.py` | `/opt/mt5-crs/src/execution/` | 风险监控（Task #105） | ✅ |
| `src/gateway/mt5_client.py` | `/opt/mt5-crs/src/gateway/` | ZMQ 客户端 | ✅ |
| `src/risk/circuit_breaker.py` | `/opt/mt5-crs/src/risk/` | 熔断器（Task #104） | ✅ |
| `config/mt5_connection.yaml` | `/opt/mt5-crs/config/` | 连接配置 | ✅ |
| `config/risk_config.yaml` | `/opt/mt5-crs/config/` | 风险配置 | ✅ |
| `scripts/verify/verify_mt5_live_connector.py` | `/opt/mt5-crs/scripts/verify/` | 验证脚本 | 🟡 可选 |

**部署命令示例**:
```bash
# 方式 1: Git 拉取（推荐）
cd /opt/mt5-crs
git pull origin main
git checkout main

# 方式 2: rsync 同步（从开发机）
rsync -avz --progress \
    /path/to/dev/mt5-crs/src/execution/*.py \
    user@172.19.141.250:/opt/mt5-crs/src/execution/

# 方式 3: scp 复制
scp src/execution/mt5_live_connector.py user@172.19.141.250:/opt/mt5-crs/src/execution/
```

**验证文件完整性**:
```bash
# 检查关键文件是否存在
required_files=(
    "/opt/mt5-crs/src/execution/mt5_live_connector.py"
    "/opt/mt5-crs/src/execution/heartbeat_monitor.py"
    "/opt/mt5-crs/src/execution/secure_loader.py"
    "/opt/mt5-crs/src/gateway/mt5_client.py"
    "/opt/mt5-crs/config/mt5_connection.yaml"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ MISSING: $file"
    fi
done
```

---

### 2.2 Windows GTW 节点文件清单

| 源路径（仓库） | 目标路径（GTW 节点） | 用途 | 必需 |
|---------------|---------------------|------|------|
| `scripts/gateway/mt5_zmq_server.py` | `C:\mt5-crs\scripts\gateway\` | ZMQ 服务器 | ✅ |
| `config/mt5_connection.yaml` | `C:\mt5-crs\config\` | 连接配置 | ✅ |
| `scripts/gateway/test_mt5_zmq_server.py` | `C:\mt5-crs\scripts\gateway\` | 测试脚本 | 🟡 可选 |

**部署命令示例**（PowerShell）:
```powershell
# 方式 1: Git 拉取
cd C:\mt5-crs
git pull origin main

# 方式 2: SCP 从 Linux 推送（在 Linux 上执行）
scp scripts/gateway/mt5_zmq_server.py user@172.19.141.249:C:/mt5-crs/scripts/gateway/

# 方式 3: 手动复制（通过远程桌面）
# 从开发机复制文件到 GTW 节点
```

**验证文件完整性**（PowerShell）:
```powershell
$required_files = @(
    "C:\mt5-crs\scripts\gateway\mt5_zmq_server.py",
    "C:\mt5-crs\config\mt5_connection.yaml"
)

foreach ($file in $required_files) {
    if (Test-Path $file) {
        Write-Host "✅ $file"
    } else {
        Write-Host "❌ MISSING: $file" -ForegroundColor Red
    }
}
```

---

## 第三阶段：配置文件同步

### 3.1 mt5_connection.yaml 配置

**通用配置模板**（适用于 Linux Inf 和 Windows GTW）:

```yaml
# MT5 连接配置 - Protocol v4.3
# 文件路径: /opt/mt5-crs/config/mt5_connection.yaml (Linux)
#           C:\mt5-crs\config\mt5_connection.yaml (Windows)

# ============================================================================
# Windows GTW 节点配置（仅在 Windows 上使用）
# ============================================================================
mt5:
  # MT5 账户信息
  login: 12345678                   # 替换为真实 MT5 账号
  password: "your_password"          # 替换为真实密码
  server: "Broker-Server"            # 替换为经纪商服务器名称

  # MT5 终端路径（自动检测，通常无需修改）
  terminal_path: "C:\\Program Files\\MetaTrader 5\\terminal64.exe"

  # 连接超时（毫秒）
  timeout_ms: 60000                  # 60 秒

# ============================================================================
# ZMQ 服务器配置（Windows GTW）
# ============================================================================
zmq_server:
  # 监听端口
  port: 5555

  # 绑定地址（* 表示监听所有网络接口，0.0.0.0 同义）
  bind_address: "*"

  # 请求超时（毫秒）
  timeout_ms: 5000                   # 5 秒

  # 高水位标记（ZMQ 队列大小）
  high_water_mark: 1000

# ============================================================================
# ZMQ 客户端配置（Linux Inf）
# ============================================================================
mt5_client:
  # Windows GTW 地址
  gtw_address: "tcp://172.19.141.249:5555"

  # 连接超时（毫秒）
  timeout_ms: 5000                   # 5 秒

  # 重试策略
  retry_attempts: 3                  # 重试 3 次
  retry_delay_ms: 1000               # 每次重试间隔 1 秒

  # 心跳配置
  heartbeat:
    interval_seconds: 5              # 每 5 秒 PING 一次
    failure_threshold: 3             # 连续失败 3 次触发熔断
    auto_restart: true               # 熔断后自动重启心跳

# ============================================================================
# 安全配置（Windows GTW）
# ============================================================================
security:
  # IP 白名单（仅允许来自这些 IP 的连接）
  allowed_ips:
    - "172.19.141.250"               # Linux Inf 节点 IP
    - "127.0.0.1"                    # 本地测试

  # Risk Signature 验证
  require_signature: true            # 强制要求 Risk Signature
  signature_expiry_seconds: 2        # 签名有效期 2 秒
  signature_algorithm: "sha256"      # 签名算法

  # TLS 加密（可选，使用 CurveZMQ）
  enable_tls: false                  # 默认关闭
  server_secret_key: ""              # CurveZMQ 服务器私钥
  server_public_key: ""              # CurveZMQ 服务器公钥

# ============================================================================
# 日志配置
# ============================================================================
logging:
  # 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
  level: "INFO"

  # 日志文件路径
  file:
    linux: "/var/log/mt5_crs/mt5_live_connector.log"
    windows: "C:\\mt5-crs\\logs\\mt5_zmq_server.log"

  # 日志格式
  format: "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"

  # 日志轮转（可选）
  rotation:
    max_bytes: 10485760              # 10MB
    backup_count: 5                  # 保留 5 个历史文件

# ============================================================================
# 性能配置
# ============================================================================
performance:
  # 订单执行超时（毫秒）
  order_timeout_ms: 10000            # 10 秒

  # 最大并发订单数
  max_concurrent_orders: 10

  # ZMQ IO 线程数
  zmq_io_threads: 2
```

**配置同步步骤**:

1. **编辑配置文件**（在开发机）:
   ```bash
   vim /opt/mt5-crs/config/mt5_connection.yaml
   # 修改 MT5 账户信息、GTW IP 等
   ```

2. **同步到 Linux Inf**:
   ```bash
   scp config/mt5_connection.yaml user@172.19.141.250:/opt/mt5-crs/config/
   ```

3. **同步到 Windows GTW**:
   ```bash
   scp config/mt5_connection.yaml user@172.19.141.249:C:/mt5-crs/config/
   ```

4. **验证配置文件**:
   ```bash
   # Linux Inf
   python3 -c "import yaml; yaml.safe_load(open('/opt/mt5-crs/config/mt5_connection.yaml'))"

   # Windows GTW
   python -c "import yaml; yaml.safe_load(open('C:/mt5-crs/config/mt5_connection.yaml'))"
   ```

---

### 3.2 risk_config.yaml 配置

**仅用于 Linux Inf 节点**（RiskMonitor 配置）:

```yaml
# 风险监控配置 - Task #105
# 文件路径: /opt/mt5-crs/config/risk_config.yaml

risk_monitor:
  # 单笔订单最大手数
  max_position_size: 1.0             # 1 标准手

  # 最大持仓数
  max_open_positions: 5

  # 最大日内亏损（美元）
  max_daily_loss: 1000.0

  # 最大杠杆倍数
  max_leverage: 100

  # 保证金水平阈值（百分比）
  min_margin_level: 200.0            # 200%

  # Risk Signature 配置
  signature:
    algorithm: "sha256"
    salt: "MT5_CRS_SALT_2026"        # 替换为随机字符串
    expiry_seconds: 2                # 2 秒有效期
```

**部署命令**:
```bash
scp config/risk_config.yaml user@172.19.141.250:/opt/mt5-crs/config/
```

---

## 第四阶段：防火墙配置

### 4.1 Linux Inf 节点防火墙

**CentOS/RHEL (firewalld)**:
```bash
# 无需开放入站端口（Inf 是客户端，仅出站连接到 GTW）
# 但需确保出站 5555 端口未被阻止

# 检查防火墙状态
sudo firewall-cmd --state

# 允许出站连接（通常默认允许）
sudo firewall-cmd --permanent --direct --add-rule ipv4 filter OUTPUT 0 -p tcp --dport 5555 -j ACCEPT
sudo firewall-cmd --reload
```

**Ubuntu (ufw)**:
```bash
# 允许出站连接到 GTW
sudo ufw allow out to 172.19.141.249 port 5555 proto tcp
sudo ufw reload
```

**验证连通性**:
```bash
# 测试 TCP 连接
telnet 172.19.141.249 5555

# 或使用 netcat
nc -zv 172.19.141.249 5555
```

---

### 4.2 Windows GTW 节点防火墙

**方式 1: PowerShell 命令（推荐）**:
```powershell
# 以管理员身份运行 PowerShell

# 允许 TCP 5555 入站（仅来自 Linux Inf IP）
New-NetFirewallRule -DisplayName "MT5 ZMQ Server Port 5555" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 5555 `
    -Action Allow `
    -RemoteAddress 172.19.141.250 `
    -Profile Domain,Private

# 验证规则
Get-NetFirewallRule -DisplayName "MT5 ZMQ Server Port 5555" | Format-List
```

**方式 2: 图形界面配置**:
1. 打开 `控制面板` > `Windows Defender 防火墙` > `高级设置`
2. 左侧点击 `入站规则`，右侧点击 `新建规则`
3. 选择 `端口` > `下一步`
4. 选择 `TCP`，特定本地端口填入 `5555` > `下一步`
5. 选择 `允许连接` > `下一步`
6. 勾选 `域`、`专用`、`公用` > `下一步`
7. 名称填入 `MT5 ZMQ Server Port 5555` > `完成`

**验证防火墙规则**:
```powershell
# 检查端口是否监听
netstat -an | findstr 5555

# 测试从 Linux Inf 连接（在 Linux 上执行）
telnet 172.19.141.249 5555
```

---

## 第五阶段：验证步骤

### 5.1 Windows GTW 端验证

#### Step 1: 启动 MT5 ZMQ Server

```powershell
cd C:\mt5-crs
python scripts\gateway\mt5_zmq_server.py
```

**预期输出**:
```
[2026-01-15 10:00:00,000] [INFO] MT5 ZMQ Server starting...
[2026-01-15 10:00:00,123] [INFO] MT5 initialized successfully
[2026-01-15 10:00:00,234] [INFO] Account: 12345678, Balance: 100000.00 USD
[2026-01-15 10:00:00,345] [INFO] ZMQ REP socket bound to tcp://*:5555
[2026-01-15 10:00:00,456] [INFO] Server ready, waiting for requests...
```

#### Step 2: 本地连接测试（Windows 本机）

```powershell
# 使用测试脚本
python scripts\gateway\test_mt5_zmq_server.py

# 或手动测试
python -c "import zmq; ctx = zmq.Context(); sock = ctx.socket(zmq.REQ); sock.connect('tcp://127.0.0.1:5555'); sock.send_json({'action': 'PING'}); print(sock.recv_json())"
```

**预期输出**:
```json
{
  "status": "ok",
  "server_time": "2026-01-15T10:05:00.123456Z",
  "latency_ms": 0.5
}
```

---

### 5.2 Linux Inf 端验证

#### Step 1: 测试网络连通性

```bash
# 测试 TCP 连接
telnet 172.19.141.249 5555

# 或使用 Python ZMQ
python3 -c "
import zmq
ctx = zmq.Context()
sock = ctx.socket(zmq.REQ)
sock.setsockopt(zmq.RCVTIMEO, 5000)
sock.connect('tcp://172.19.141.249:5555')
sock.send_json({'action': 'PING'})
print(sock.recv_json())
"
```

#### Step 2: 测试 MT5Client

```bash
python3 -c "
from src.gateway.mt5_client import MT5Client
client = MT5Client(server_address='tcp://172.19.141.249:5555')
response = client.ping()
print(f'PING: {response}')
"
```

#### Step 3: 测试 MT5LiveConnector

```bash
python3 -c "
from src.execution.mt5_live_connector import MT5LiveConnector
connector = MT5LiveConnector(
    gtw_address='tcp://172.19.141.249:5555',
    risk_config_path='/opt/mt5-crs/config/risk_config.yaml'
)
response = connector.ping()
print(f'Connector PING: {response}')
"
```

#### Step 4: 测试订单执行（0.01 手）

```bash
python3 -c "
from src.execution.mt5_live_connector import MT5LiveConnector

connector = MT5LiveConnector(
    gtw_address='tcp://172.19.141.249:5555',
    risk_config_path='/opt/mt5-crs/config/risk_config.yaml'
)

order = {
    'symbol': 'EURUSD',
    'type': 'BUY',
    'volume': 0.01,
    'price': 0.0,
    'sl': 1.05000,
    'tp': 1.06000,
    'comment': 'TEST_DEPLOYMENT'
}

response = connector.open_order(order)
print(f'Order Response: {response}')
"
```

**预期输出**:
```json
{
  "status": "FILLED",
  "ticket": 12345678,
  "symbol": "EURUSD",
  "volume": 0.01,
  "price": 1.05230,
  "latency_ms": 45.67
}
```

---

### 5.3 完整集成测试

运行物理验证脚本：

```bash
# Linux Inf 端执行
python3 /opt/mt5-crs/scripts/verify/verify_mt5_live_connector.py \
    --gtw-address tcp://172.19.141.249:5555 \
    --mode full
```

**预期输出**:
```
[INFO] Starting MT5 Live Bridge verification...
[INFO] Test 1/5: PING connectivity... ✅ PASS (2.34ms)
[INFO] Test 2/5: GET_ACCOUNT query... ✅ PASS
[INFO] Test 3/5: OPEN order (0.01 lot)... ✅ PASS (45.67ms)
[INFO] Test 4/5: GET_POSITIONS query... ✅ PASS
[INFO] Test 5/5: CLOSE order... ✅ PASS (38.92ms)
[INFO] ══════════════════════════════════════════════════
[INFO] All tests passed ✅
[INFO] Total latency (P95): 42.30ms
```

---

## 第六阶段：生产部署

### 6.1 进程守护配置

#### Linux Inf (systemd)

创建服务文件 `/etc/systemd/system/mt5-live-connector.service`:

```ini
[Unit]
Description=MT5 Live Connector - Zero-Trust Trading Bridge
After=network.target

[Service]
Type=simple
User=mt5user
Group=mt5user
WorkingDirectory=/opt/mt5-crs
Environment="PYTHONPATH=/opt/mt5-crs"
Environment="MT5_GTW_ADDRESS=tcp://172.19.141.249:5555"
Environment="MT5_RISK_CONFIG=/opt/mt5-crs/config/risk_config.yaml"
Environment="MT5_LOG_FILE=/var/log/mt5_crs/mt5_live_connector.log"
ExecStart=/opt/mt5-crs/venv/bin/python3 src/execution/mt5_live_connector.py --mode=production
Restart=always
RestartSec=10
StandardOutput=append:/var/log/mt5_crs/mt5_live_connector.log
StandardError=append:/var/log/mt5_crs/mt5_live_connector_error.log

[Install]
WantedBy=multi-user.target
```

**启动服务**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mt5-live-connector
sudo systemctl start mt5-live-connector
sudo systemctl status mt5-live-connector
```

---

#### Windows GTW (NSSM)

**下载 NSSM**: https://nssm.cc/download

```powershell
# 安装服务
.\nssm.exe install MT5ZmqServer "C:\Python39\python.exe" "C:\mt5-crs\scripts\gateway\mt5_zmq_server.py"

# 配置工作目录
.\nssm.exe set MT5ZmqServer AppDirectory "C:\mt5-crs"

# 配置日志
.\nssm.exe set MT5ZmqServer AppStdout "C:\mt5-crs\logs\mt5_zmq_server.log"
.\nssm.exe set MT5ZmqServer AppStderr "C:\mt5-crs\logs\mt5_zmq_server_error.log"

# 配置重启策略
.\nssm.exe set MT5ZmqServer AppRestartDelay 10000  # 10秒后重启

# 启动服务
.\nssm.exe start MT5ZmqServer

# 检查服务状态
Get-Service MT5ZmqServer
```

---

### 6.2 日志轮转配置

#### Linux Inf (logrotate)

创建 `/etc/logrotate.d/mt5-crs`:

```
/var/log/mt5_crs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 mt5user mt5user
    postrotate
        systemctl reload mt5-live-connector > /dev/null 2>&1 || true
    endscript
}
```

**测试轮转**:
```bash
sudo logrotate -f /etc/logrotate.d/mt5-crs
ls -lh /var/log/mt5_crs/
```

---

## 第七阶段：监控告警

### 7.1 心跳监控告警

**脚本**: `/opt/mt5-crs/scripts/monitor_heartbeat.sh`

```bash
#!/bin/bash
# 监控心跳失败并发送告警

LOG_FILE="/var/log/mt5_crs/mt5_live_connector.log"
ALERT_EMAIL="admin@example.com"

tail -f "$LOG_FILE" | while read line; do
    if echo "$line" | grep -q "HEARTBEAT FAILURE"; then
        echo "ALERT: MT5 Heartbeat Failure at $(date)" | \
            mail -s "[CRITICAL] MT5 Heartbeat Failure" "$ALERT_EMAIL"
    fi
done
```

**启动监控**:
```bash
nohup /opt/mt5-crs/scripts/monitor_heartbeat.sh > /dev/null 2>&1 &
```

---

### 7.2 性能监控脚本

**脚本**: `/opt/mt5-crs/scripts/monitor_performance.py`

```python
#!/usr/bin/env python3
import time
from src.execution.mt5_live_connector import MT5LiveConnector

connector = MT5LiveConnector(gtw_address="tcp://172.19.141.249:5555")

while True:
    try:
        start = time.time()
        response = connector.ping()
        latency = (time.time() - start) * 1000

        if latency > 50:  # 超过 50ms 告警
            print(f"[WARNING] High latency: {latency:.2f}ms")

        time.sleep(10)  # 每 10 秒检测一次
    except Exception as e:
        print(f"[ERROR] PING failed: {e}")
        time.sleep(30)
```

---

## 附录：故障排查清单

| 故障现象 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `zmq.error.Again` | GTW 服务器未启动 | 启动 mt5_zmq_server.py |
| `Connection refused` | 防火墙阻止 5555 端口 | 配置防火墙规则 |
| `MISSING_SIGNATURE` | 订单未经过 RiskMonitor | 使用 MT5LiveConnector.open_order() |
| `MT5 initialization failed` | MT5 终端未登录 | 登录 MT5 账户 |
| `HEARTBEAT FAILURE` | 网络断开或 GTW 崩溃 | 重启 GTW 服务器 |

---

**文档版本**: v1.0
**最后更新**: 2026-01-15
**Protocol**: v4.3 (Zero-Trust Edition)
**作者**: Claude Sonnet 4.5 (MT5-CRS Hub Agent)

**END OF SYNC GUIDE**
