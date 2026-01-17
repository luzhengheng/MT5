# Task #107 部署变更清单

## 概述

此文档记录 Task #107 引入的所有部署变更，便于同步到其他环境。

## 环境变量 (ENV)

### 新增环境变量

```bash
# 风险管理配置 (在 src/config/__init__.py 中定义)
export RISK_MAX_DAILY_LOSS=100.0
export RISK_MAX_ORDER_RATE=100
export RISK_MAX_POSITION_SIZE=10000.0
export RISK_WEBHOOK_URL=""

# 文件锁目录 (Kill Switch 和 Log 目录)
export MT5_CRS_LOCK_DIR=/var/run/mt5_crs
export MT5_CRS_LOG_DIR=/var/log/mt5_crs
```

### 环境变量验证

```bash
# 检查环境变量是否设置
echo "RISK_MAX_DAILY_LOSS=$RISK_MAX_DAILY_LOSS"
echo "MT5_CRS_LOCK_DIR=$MT5_CRS_LOCK_DIR"
```

## 依赖包 (Dependencies)

### Python 依赖

新增或更新的包:

```bash
# ZeroMQ Python 绑定 (如果未安装)
pip install pyzmq>=23.0

# 标准库依赖 (Python 3.8+ 已内置):
# - threading
# - collections (deque)
# - zmq (pyzmq)
# - json
# - logging
# - time
# - signal
# - sys
```

### 安装命令

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或仅安装新增包
pip install pyzmq>=23.0
```

### 依赖检查

```bash
# 验证 pyzmq 安装
python3 -c "import zmq; print(f'ZMQ version: {zmq.zmq_version()}')"

# 验证所有导入
python3 -c "from src.live_loop.ingestion import MarketDataReceiver; print('OK')"
```

## 文件系统 (Files)

### 新增文件

```
src/live_loop/
├── __init__.py               (新建，可为空)
├── ingestion.py              (420 行，市场数据接收器)
└── main.py                   (340 行，Live Loop 主程序)

scripts/tools/
├── __init__.py               (新建，可为空)
└── listen_zmq_pub.py         (280 行，协议侦察脚本)

scripts/
└── audit_task_107.py         (450 行，TDD 审计脚本)

tests/
└── test_live_loop_ingestion.py (基本单元测试)

docs/archive/tasks/TASK_107_DATA_INGESTION/
├── COMPLETION_REPORT.md      (完成报告)
├── QUICK_START.md            (快速启动指南)
├── SYNC_GUIDE.md             (本文件)
└── VERIFY_LOG.log            (审计日志)
```

### 修改的文件

```
src/config/__init__.py
├── 新增常量: KILL_SWITCH_LOCK_DIR, KILL_SWITCH_LOCK_FILE
├── 新增常量: RISK_MAX_DAILY_LOSS, RISK_MAX_ORDER_RATE, RISK_MAX_POSITION_SIZE, RISK_WEBHOOK_URL
└── 更新 __all__ 列表
```

### 目录结构

确保以下目录存在:

```bash
# 创建必要的目录
mkdir -p src/live_loop
mkdir -p scripts/tools
mkdir -p tests
mkdir -p docs/archive/tasks/TASK_107_DATA_INGESTION
mkdir -p /var/run/mt5_crs        # Kill Switch 锁文件目录
mkdir -p /var/log/mt5_crs        # 日志目录 (如需)

# 设置权限
chmod 755 /var/run/mt5_crs
chmod 755 /var/log/mt5_crs
```

## 配置文件 (Configuration)

### ZMQ 配置

在 `src/live_loop/ingestion.py` 中配置:

```python
# 生产环境配置
ZMQ_INTERNAL_IP = "172.19.141.255"  # Windows Gateway 内网 IP
ZMQ_DATA_PORT = 5556                # 行情推送端口

# 本地开发配置 (可选)
# ZMQ_INTERNAL_IP = "localhost"
# ZMQ_DATA_PORT = 5556
```

### Kill Switch 配置

在环境变量或 `.env` 文件中配置:

```bash
# Linux 系统
MT5_CRS_LOCK_DIR=/var/run/mt5_crs

# Windows 系统 (如适用)
MT5_CRS_LOCK_DIR=C:\Windows\Temp\mt5_crs
```

### 日志配置

在 `src/live_loop/main.py` 中配置:

```python
logging.basicConfig(
    level=logging.INFO,  # 或 logging.DEBUG
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('VERIFY_LOG.log', mode='a')
    ]
)
```

## SQL 迁移 (Database)

**无数据库迁移** - Task #107 不涉及数据库变更。

## 网络配置 (Network)

### 防火墙规则

确保以下网络连接畅通:

```bash
# Linux Inf -> Windows GTW (ZMQ PUB)
# 源: Linux Inf (172.19.141.250)
# 目标: Windows GTW (172.19.141.255:5556)
# 协议: TCP
# 方向: 出站

# 规则名称
iptables -A OUTPUT -d 172.19.141.255 -p tcp --dport 5556 -j ACCEPT
```

### 端口检查

```bash
# 检查 ZMQ 端口是否可达
nc -zv 172.19.141.255 5556

# 或使用 telnet
telnet 172.19.141.255 5556

# 或使用 Python
python3 -c "
import zmq
ctx = zmq.Context()
sock = ctx.socket(zmq.SUB)
sock.connect('tcp://172.19.141.255:5556')
print('✅ Connected')
"
```

## 权限配置 (Permissions)

### 文件权限

```bash
# 源代码权限
chmod 644 src/live_loop/ingestion.py
chmod 644 src/live_loop/main.py
chmod 755 scripts/tools/listen_zmq_pub.py
chmod 755 scripts/audit_task_107.py

# 测试文件权限
chmod 644 tests/test_live_loop_ingestion.py

# 文档权限
chmod 644 docs/archive/tasks/TASK_107_DATA_INGESTION/*
```

### 进程权限

```bash
# Live Loop 通常以应用用户身份运行
# 示例: 以 trading 用户身份运行
sudo -u trading python3 -m src.live_loop.main

# 或使用 systemd 服务
[Service]
User=trading
Group=trading
WorkingDirectory=/opt/mt5-crs
ExecStart=/usr/bin/python3 -m src.live_loop.main
```

## 部署步骤 (Deployment Steps)

### 1. 代码同步

```bash
# 进入项目目录
cd /opt/mt5-crs

# 拉取最新代码
git pull origin main
# 或
git pull origin feat/task-107

# 确认代码已更新
git log -1 --oneline
# 应显示: feat(task-107): Strategy Engine Live Data Ingestion...
```

### 2. 环境准备

```bash
# 设置环境变量
export RISK_MAX_DAILY_LOSS=100.0
export RISK_MAX_ORDER_RATE=100
export RISK_MAX_POSITION_SIZE=10000.0
export MT5_CRS_LOCK_DIR=/var/run/mt5_crs
export MT5_CRS_LOG_DIR=/var/log/mt5_crs

# 或写入 .env 文件
cat > .env << EOF
RISK_MAX_DAILY_LOSS=100.0
RISK_MAX_ORDER_RATE=100
RISK_MAX_POSITION_SIZE=10000.0
RISK_WEBHOOK_URL=
MT5_CRS_LOCK_DIR=/var/run/mt5_crs
MT5_CRS_LOG_DIR=/var/log/mt5_crs
EOF

# 加载 .env
set -a
source .env
set +a
```

### 3. 依赖安装

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 或手动安装
pip install pyzmq>=23.0

# 验证
python3 -c "import zmq; print(f'ZMQ {zmq.zmq_version()}')"
```

### 4. 目录创建

```bash
# 创建必要的目录
mkdir -p src/live_loop
mkdir -p scripts/tools
mkdir -p /var/run/mt5_crs
mkdir -p /var/log/mt5_crs
chmod 755 /var/run/mt5_crs
chmod 755 /var/log/mt5_crs
```

### 5. 配置验证

```bash
# 运行 TDD 审计
python3 scripts/audit_task_107.py

# 预期输出:
# [GATE1] ✅ Gate 1 审计通过
# Gate 1 审计通过
```

### 6. 启动测试

```bash
# 协议侦察 (测试连接)
python3 scripts/tools/listen_zmq_pub.py --timeout 10

# 预期输出:
# [RECONNAISSANCE] ✅ 成功连接到 tcp://172.19.141.255:5556
# [LIVE_TICK] 收到第 1 条数据: ...
```

### 7. 生产启动

```bash
# 启动 Live Loop
python3 -m src.live_loop.main

# 或使用部署脚本
bash deploy/launch_task_104_production.sh

# 预期输出:
# [LiveLoop] ✅ Live Loop 已启动
# [LiveLoop] 进入主循环...
```

## 回滚计划 (Rollback)

### 快速回滚

```bash
# 回滚到上一个提交
git revert HEAD

# 或硬重置 (谨慎使用)
git reset --hard HEAD~1

# 重新启动应用
python3 -m src.live_loop.main
```

### 备份恢复

```bash
# 备份当前代码
cp -r src/live_loop src/live_loop.backup

# 还原备份
rm -rf src/live_loop
mv src/live_loop.backup src/live_loop
```

## 验证清单 (Verification Checklist)

部署完成后，请验证以下项目:

- [ ] Git 代码已更新 (`git log` 显示 Task #107 提交)
- [ ] 环境变量已设置 (`echo $RISK_MAX_DAILY_LOSS`)
- [ ] 依赖已安装 (`pip show pyzmq`)
- [ ] 目录结构正确 (`ls -la src/live_loop/`)
- [ ] 文件权限正确 (`ls -la scripts/audit_task_107.py`)
- [ ] TDD 审计通过 (`python3 scripts/audit_task_107.py`)
- [ ] 协议侦察成功 (`python3 scripts/tools/listen_zmq_pub.py --timeout 10`)
- [ ] Live Loop 启动成功 (查看日志中的启动信息)
- [ ] 数据接收正常 (查看 `[LIVE_TICK]` 日志)
- [ ] 心跳任务正常 (查看 `[Heartbeat]` 日志)

## 监控和告警 (Monitoring)

### 关键指标

监控以下指标:

```bash
# Tick 接收速率 (应该 > 0)
grep "\[LIVE_TICK\]" VERIFY_LOG.log | wc -l

# 数据饥饿告警 (应该为 0)
grep "DATA_STARVED" VERIFY_LOG.log | wc -l

# 错误日志 (应该为 0)
grep "ERROR" VERIFY_LOG.log | wc -l

# 熔断状态 (应该是 SAFE)
grep "Circuit Breaker" VERIFY_LOG.log | tail -1
```

### 告警规则

```bash
# 告警: 30 分钟无数据
# 告警: 连续 3 个错误
# 告警: 熔断器触发
# 告警: 内存占用 > 100MB
```

## 性能基准 (Baseline)

部署后的预期性能:

| 指标 | 预期值 | 告警阈值 |
|------|--------|----------|
| Tick 接收延迟 | 10-50ms | > 200ms |
| 主循环延迟 | 10ms | > 50ms |
| 缓冲区大小 | 10-100 条 | > 500 条 |
| 内存占用 | 30-50MB | > 100MB |
| CPU 占用 | 2-5% | > 20% |
| 错误率 | 0% | > 1% |

## 常见问题 (FAQ)

### Q: 如何在 Windows 环境中运行?

A: Task #107 在 Linux 上开发，Windows 支持需要:
1. 安装 Windows 版 Python 3.8+
2. 安装 pyzmq: `pip install pyzmq`
3. 更新 ZMQ IP 配置
4. 修改路径配置 (使用 `\` 而不是 `/`)

### Q: 如何处理 ZMQ 连接断开?

A: 系统会自动:
1. 记录警告日志
2. 触发数据饥饿告警
3. 在 10s 后重新连接

### Q: 如何扩展到多个市场数据源?

A: 修改 `MarketDataReceiver`:
1. 支持多个 ZMQ 连接
2. 在缓冲区中标记数据源
3. 在轮询时根据数据源路由

## 相关文档

- [完成报告](./COMPLETION_REPORT.md) - 详细信息
- [快速启动](./QUICK_START.md) - 运行指南
- [验证日志](./VERIFY_LOG.log) - 审计记录

---

**文档生成**: 2026-01-15 13:13:30 UTC
**Protocol 版本**: v4.3 (Zero-Trust Edition)
**最后更新**: Task #107 完成
